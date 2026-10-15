"""Read-only, offline inspection of already-present pinned runtime artifacts.

Does not create/start containers, contact registries, run project code or inspect
old server data/log volumes. Stdlib + existing docker/zstd executables only.
Writes a new evidence JSON path, refusing overwrite. Do not publish binaries.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import zipfile

IMAGES = {
    "server": "sonarqube@sha256:9026624a61cd25542a402a9e7213dd7dbb39724ac9597e331e6b85362558c079",
    "scanner": "sonarsource/sonar-scanner-cli@sha256:23ca0f137965d9dff2198074043fd48d386280bc5d0ccac8c8349cea4cf096a9",
    "build": "maven@sha256:e4a7ace3dc0d645ed97f8d9ad0b0d3f0b14fa8d150138f27f116d7105a639b82",
}
OLD = "264185299cf7f1ad4a2784e6845c476dd4d9f2745e8de84b42905bac8a4bcba3"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(*args):
    return subprocess.check_output(args, timeout=120, stderr=subprocess.PIPE)


def image_files(image):
    """Stream existing local OCI archive. No extraction or execution of image code."""
    process = subprocess.Popen(["docker", "image", "save", image], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    records, metadata = [], []
    try:
        with tarfile.open(fileobj=process.stdout, mode="r|*") as outer:
            for member in outer:
                if not member.isfile():
                    continue
                if member.size > 600_000_000:
                    raise ValueError("Offline layer inspection exceeds fixed 600MB member bound")
                data = outer.extractfile(member).read()
                if member.name in ("manifest.json", "index.json"):
                    metadata.append(dict(path=member.name, value=json.loads(data)))
                if not member.name.startswith("blobs/") or len(data) < 512 or data[:1] in (b"{", b"["):
                    continue
                # Docker may store OCI zstd layers. Use the existing executable;
                # never install a decoder or persist/extract the image filesystem.
                encoding = "tar/gzip"
                if data[:4] == b"\x28\xb5\x2f\xfd":
                    if not shutil.which("zstd"):
                        raise ValueError("Existing zstd decoder unavailable")
                    data = subprocess.check_output(["zstd", "-d", "-c"], input=data, timeout=60, stderr=subprocess.PIPE)
                    encoding = "zstd"
                try:
                    inner = tarfile.open(fileobj=io.BytesIO(data), mode="r:*")
                except tarfile.ReadError:
                    continue
                with inner:
                    for item in inner:
                        name = item.name.lstrip("./")
                        wanted = (name.endswith("/release") and ("jdk" in name or "jvm" in name)) or name.endswith(("/bin/java", "/bin/mvn")) or ("maven-core-" in name and name.endswith(".jar")) or ("sonar-scanner" in name and name.endswith((".jar", "/sonar-scanner", "/sonar-scanner.properties")))
                        if not wanted or not item.isfile() or item.size > 40_000_000:
                            continue
                        content = inner.extractfile(item).read()
                        row = dict(path=name, layer=member.name, layer_encoding=encoding, size_bytes=len(content), sha256=sha(content))
                        if name.endswith("/release"):
                            row["release"] = content.decode()
                        if name.endswith(".jar"):
                            with zipfile.ZipFile(io.BytesIO(content)) as jar:
                                row["jar_manifest"] = jar.read("META-INF/MANIFEST.MF").decode()
                                row["pom_properties"] = {p:jar.read(p).decode() for p in jar.namelist() if p.endswith("pom.properties") and ("/maven-core/" in p or "sonarsource" in p)}
                        records.append(row)
    finally:
        process.stdout.close()
        error = process.stderr.read()
        code = process.wait(timeout=120)
    if code:
        raise RuntimeError(error.decode())
    return dict(files=records, archive_metadata=metadata, executed=False)


def container_file(path):
    data = run("docker", "cp", OLD + ":" + path, "-")
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        files = [v for v in archive if v.isfile()]
        if len(files) != 1:
            raise ValueError("Expected one static artifact")
        return archive.extractfile(files[0]).read()


def inspect():
    images = {}
    for role, image in IMAGES.items():
        row = json.loads(run("docker", "image", "inspect", image))[0]
        if row["Id"] != "sha256:" + image.split("sha256:")[1]:
            raise ValueError("Pinned local image identity changed")
        # Only explicitly safe version metadata; never dump all Env/credentials.
        env = {v.split("=",1)[0]:v.split("=",1)[1] for v in row["Config"].get("Env",[]) if v.split("=",1)[0] in ("JAVA_HOME","JAVA_VERSION","MAVEN_HOME","SONAR_VERSION")}
        images[role] = dict(reference=image, image_id=row["Id"], platform=[row["Os"],row["Architecture"]], version_environment=env)
    old = json.loads(run("docker", "inspect", OLD))[0]
    if old["State"]["Running"]:
        raise ValueError("Expected stopped old server; do not alter it")
    plugins = []
    relevant = ("sonar-java-plugin-8.37.0.45887.jar", "sonar-python-plugin-5.27.0.35548.jar", "sonar-javascript-plugin-13.4.0.43982-multi.jar")
    for filename in relevant:
        data = container_file("/opt/sonarqube/lib/extensions/"+filename)
        with zipfile.ZipFile(io.BytesIO(data)) as jar:
            row = dict(filename=filename, sha256=sha(data), manifest=jar.read("META-INF/MANIFEST.MF").decode())
            if "javascript" in filename:
                import lzma
                compressed=jar.read("linux-x64/node.xz")
                row["embedded_node"]=dict(version_file=jar.read("linux-x64/version.txt").decode().strip(),compressed_sha256=sha(compressed),binary_sha256=sha(lzma.decompress(compressed)),executed=False)
            plugins.append(row)
    versions = {}
    for label, args in (("java", ("java","-version")),("maven",("mvn","-version")),("node",("node","--version")),("python",("python3","--version")),("zstd",("zstd","--version"))):
        proc=subprocess.run(args,capture_output=True,timeout=20,check=True)
        versions[label]=(proc.stdout+proc.stderr).decode().strip()
    return dict(images=images,build_image_offline_files=image_files(IMAGES["build"]),
                scanner_image_offline_files=image_files(IMAGES["scanner"]),
                server_jdk_release=container_file("/opt/java/openjdk/release").decode(),plugins=plugins,
                host_versions=versions,old_server=dict(id=old["Id"],state=old["State"],image=old["Image"]),
                limitations=["Static image bytes are not runtime/build success", "No live mode/rules/permissions exported", "No historical dependency resolution or compilation", "No server/image container started"])


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",required=True);args=parser.parse_args()
    output=Path(args.output)
    if output.exists():raise ValueError("Refusing overwrite")
    result=inspect()
    output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("Offline runtime inspection recorded:",output)


if __name__=="__main__":main()
