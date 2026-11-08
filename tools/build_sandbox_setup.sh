#!/bin/sh
# Shared setup/capture recipe. This version permits no Maven command.
set -u
OUT=/output
CG=/sys/fs/cgroup
STAGE=BOOTSTRAP
COMMAND_CATEGORY=register_capture
exec 3>&1 4>&2

finish() {
    result=$1
    trap - EXIT
    trap '' TERM INT
    set +e
    printf '%s\n' "$result" > "$OUT/exit.code"
    printf '%s\n' "$STAGE" > "$OUT/stage.txt"
    printf '%s\n' "$COMMAND_CATEGORY" > "$OUT/command-category.txt"
    for metric in memory.peak memory.events cpu.stat; do
        if [ -r "$CG/$metric" ]; then
            cat "$CG/$metric" > "$OUT/$metric" || {
                rm -f "$OUT/$metric"
                printf 'read_failed\n' > "$OUT/$metric.unavailable"
            }
        else
            printf 'not_readable\n' > "$OUT/$metric.unavailable"
        fi
    done
    printf 'TD_SANDBOX_EXIT stage=%s category=%s code=%s\n' "$STAGE" "$COMMAND_CATEGORY" "$result" >&3
    printf 'TD_SETUP_STDOUT_BEGIN\n' >&3
    [ ! -f "$OUT/setup.stdout" ] || cat "$OUT/setup.stdout" >&3
    printf 'TD_SETUP_STDOUT_END\n' >&3
    printf 'TD_SETUP_STDERR_BEGIN\n' >&4
    [ ! -f "$OUT/setup.stderr" ] || cat "$OUT/setup.stderr" >&4
    printf 'TD_SETUP_STDERR_END\n' >&4
    touch "$OUT/ready"
    count=0
    while [ ! -f "$OUT/collected" ] && [ "$count" -lt "${TD_CAPTURE_HOLD_SECONDS:-15}" ]; do
        sleep 1
        count=$((count+1))
    done
    exit "$result"
}
trap 'finish "$?"' EXIT
trap 'exit 143' TERM
trap 'exit 130' INT

run_stage() {
    STAGE=$1
    COMMAND_CATEGORY=$2
    shift 2
    printf 'STAGE_START %s %s\n' "$STAGE" "$COMMAND_CATEGORY" >&3
    printf 'STAGE_START %s %s\n' "$STAGE" "$COMMAND_CATEGORY"
    "$@"
    result=$?
    if [ "$result" -ne 0 ]; then
        printf 'STAGE_FAILED %s %s exit=%s\n' "$STAGE" "$COMMAND_CATEGORY" "$result" >&2
        exit "$result"
    fi
    printf '%s\n' "$STAGE" >> "$OUT/passed-stages.txt"
}

# BEGIN_SETUP: the EXIT trap is already registered before redirects/setup.
exec > "$OUT/setup.stdout" 2> "$OUT/setup.stderr"
printf 'NOT_STARTED\n' > "$OUT/maven.state.txt"
run_stage MODE reject_non_smoke test "${1:-}" = --no-maven-smoke
run_stage IDENTITY uid_gid sh -c '[ "$(id -u):$(id -g)" = "1000:1000" ]'
run_stage CGROUP limits sh -c '
    [ "$(cat /sys/fs/cgroup/memory.max)" = "1073741824" ] &&
    [ "$(cat /sys/fs/cgroup/memory.swap.max)" = 0 ] &&
    read quota period < /sys/fs/cgroup/cpu.max &&
    [ "$quota" != max ] && [ "$quota" -le "$period" ]'
for metric in memory.max memory.swap.max cpu.max pids.max; do
    printf '%s=' "$metric"
    cat "$CG/$metric"
done > "$OUT/cgroup.limits.txt"

verify_mounts() {
    : > "$OUT/mount-ownership.txt"
    for path in /source /runtime-repository; do
        identity=$(stat -c '%u:%g:%a' "$path") || return $?
        printf '%s %s\n' "$path" "$identity" >> "$OUT/mount-ownership.txt"
        [ "$identity" = 1000:1000:1777 ] || return 31
        [ -w "$path" ] || return 32
    done
    cat /proc/self/mountinfo > "$OUT/mountinfo.txt"
}
run_stage MOUNT_OWNERSHIP stat_before_copy verify_mounts
run_stage SOURCE_COPY copy_frozen_source cp -R /inputs/source/. /source/
run_stage SOURCE_PERMISSIONS chmod_owned_files find /source -mindepth 1 -type f -exec chmod u+w -- {} +
run_stage ARTIFACT_COPY copy_verified_cache cp -R /inputs/repository/. /runtime-repository/
run_stage ARTIFACT_PERMISSIONS chmod_owned_files find /runtime-repository -mindepth 1 -type f -exec chmod u+w -- {} +
run_stage WORKING_DIRECTORY cd_source cd /source
run_stage SOURCE_HASHES verify_source sha256sum --quiet -c /inspection/source.sha256
run_stage CACHE_HASHES verify_cache sh -c 'cd /runtime-repository && sha256sum --quiet -c /inspection/cache.sha256'

verify_population() {
    [ "$(find /source -type f | wc -l)" -eq 117 ] &&
    [ "$(find /runtime-repository -type f | wc -l)" -eq 653 ] &&
    [ ! -e /source/.git ] && [ ! -e /source/target ] || return 33
    find /source -type f -printf '%P\n' | sort > "$OUT/source.paths"
    find /runtime-repository -type f -printf '%P\n' | sort > "$OUT/cache.paths"
    find /source -type f -print0 | sort -z | xargs -0 sha256sum > "$OUT/source.after.sha256"
    find /runtime-repository -type f -print0 | sort -z | xargs -0 sha256sum > "$OUT/cache.after.sha256"
}
run_stage POPULATION exact_file_sets verify_population
verify_writable() {
    [ "$(pwd -P)" = /source ] || return 34
    touch /source/.td-write-probe /runtime-repository/.td-write-probe || return $?
    rm /source/.td-write-probe /runtime-repository/.td-write-probe || return $?
    printf '%s\n' "$(pwd -P)" > "$OUT/working-directory.txt"
    for path in /source /runtime-repository; do stat -c '%n %u:%g:%a' "$path"; done
}
run_stage WRITABILITY owned_workspace verify_writable
run_stage FINAL_SOURCE_HASHES verify_unchanged_source sha256sum --quiet -c /inspection/source.sha256
run_stage FINAL_CACHE_HASHES verify_unchanged_cache sh -c 'cd /runtime-repository && sha256sum --quiet -c /inspection/cache.sha256'
printf 'true\n' > "$OUT/setup.complete"
for path in /proc/[0-9]*/comm; do
    [ ! -r "$path" ] || cat "$path"
done > "$OUT/processes.txt"
# Deliberate sentinel, independent of historical sources/plugins. No Maven path.
run_stage INJECTED_PRE_MAVEN_FAILURE deliberate_exit_73 sh -c '
    printf "TD_SMOKE_INJECTED_STDOUT\n"
    printf "TD_SMOKE_INJECTED_STDERR\n" >&2
    exit 73'
