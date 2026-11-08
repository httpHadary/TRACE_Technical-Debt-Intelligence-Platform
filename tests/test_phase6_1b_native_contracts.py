"""Fake native backends exercise adapters, never evidence of pretrained inference."""
from types import SimpleNamespace as NS
import numpy as np
import torch
import pytest
from forecasting_research.phase6_1b.adapters import TTM512, TimesFM512
from forecasting_research.phase6_1b.population import history, Spec


class FakeTTM(torch.nn.Module):
    def __init__(self, length=96):
        super().__init__()
        self.length=length
        self.config=NS(context_length=512,prediction_length=96,resolution_prefix_tuning=True,loss='mse',multi_quantile_head=False)

    def forward(self, **kwargs):
        return NS(prediction_outputs=torch.full((1,self.length,1),4.))


def test_ttm_native_96_point_semantics_and_input_trace():
    req=history(Spec('constant',0));a=TTM512(FakeTTM(),8)
    result=a.predict(req)
    assert len(result['path'])==90 and result['path'][89]['point']==4
    assert a.forward_receipt['native_steps']==96
    assert len(a.forward_receipt['raw_native_point_path'])==96
    assert a.forward_receipt['trace'][0]['shape']==[1,512,1]
    assert result['path'][0]['q10'] is None


def test_ttm_wrong_native_shape_fatal():
    with pytest.raises(ValueError):TTM512(FakeTTM(90),8).predict(history(Spec('constant',0)))


class FakeTimesFM:
    def __init__(self, cross=False, nan=False):
        self.forecast_config=NS(max_context=512,max_horizon=128,fix_quantile_crossing=False,infer_is_positive=False,force_flip_invariance=False)
        self.compiled_decode=self.decode
        self.cross,self.nan=cross,nan

    def decode(self,horizon,inputs,masks):
        full=np.tile(np.arange(10,dtype=float),(1,90,1))
        if self.cross:full[0,29,2]=4.5 # inner-decile crossing, q10/q50/q90 remain ordered
        if self.nan:full[0,89,0]=float('nan')
        return full[:,:,5],full

    def forecast(self,horizon,inputs):
        return self.compiled_decode(horizon,[inputs[0]],[np.zeros(512,dtype=bool)])


def test_timesfm_q50_and_native_quantile_indices():
    a=TimesFM512(FakeTimesFM());r=a.predict(history(Spec('constant',0)))
    assert r['path'][0]['raw_point']==5
    assert [r['path'][0][k] for k in ('raw_q10','raw_q50','raw_q90')]==[1,5,9]
    assert a.forward_receipt['configured_max_horizon']==128
    assert len(a.forward_receipt['raw_all_deciles'])==90


def test_timesfm_all_nine_native_quantiles_validated_without_repair():
    a=TimesFM512(FakeTimesFM(cross=True));r=a.predict(history(Spec('constant',0)))
    assert r['failure']=='NATIVE_QUANTILE_CROSSING' and r['crossing_steps']==[30]
    assert r['invalid_native_quantiles'][29][2]==4.5


def test_timesfm_nonfinite_head_fatal_even_when_selected_quantiles_valid():
    with pytest.raises(ValueError):TimesFM512(FakeTimesFM(nan=True)).predict(history(Spec('constant',0)))


def test_timesfm_rejects_hidden_padding_and_restores_callable():
    model=FakeTimesFM();original=model.compiled_decode
    model.forecast=lambda horizon,inputs:model.compiled_decode(horizon,[np.zeros(512)],[np.ones(512,dtype=bool)])
    with pytest.raises(RuntimeError):TimesFM512(model).predict(history(Spec('constant',0)))
    assert model.compiled_decode==original
