import asyncio
import json
import httpx
import pytest
from flare.ai import explain
from flare.corpus import RECORDS

@pytest.mark.parametrize('payload,content_type',[
    ({'output_text':json.dumps({'claims':[{'text':'Invented source','evidence_ids':['not-in-pack'],'classification':'Unknown','limitations':[]}],'missing_information':[],'abstain':True})},'application/json'),
    ({'output_text':json.dumps({'claims':[],'missing_information':[],'abstain':True,'safe_to_breathe':True})},'application/json'),
    ({},'text/event-stream'),
    ({'error':{'message':'Unavailable'}},'application/json'),
])
def test_invalid_provider_outputs_fall_back_without_affecting_engine(monkeypatch,payload,content_type):
    monkeypatch.setenv('AI_MODE','live')
    monkeypatch.setenv('KIE_API_KEY','test-key-never-sent')
    async def post(self,*args,**kwargs):
        return httpx.Response(200,json=payload,headers={'content-type':content_type},request=httpx.Request('POST','https://example.test'))
    monkeypatch.setattr(httpx.AsyncClient,'post',post)
    result=asyncio.run(explain(RECORDS[:1]))
    assert result['mode']=='unavailable'
    assert result['claims'][0]['evidence_ids']==['flex']
    assert 'safe_to_breathe' not in result


def test_message_parser_skips_null_reasoning_and_accepts_exact_json_fence():
    from flare.ai import response_text, validate_explanation
    value={'claims':[{'text':'Droplet observations have limited scope.','evidence_ids':['flex'],'classification':'Experimental evidence','limitations':['No calibrated raw data.']}],'missing_information':[],'abstain':True}
    response={'status':'completed','output':[{'type':'reasoning','content':None},{'type':'message','content':[{'type':'output_text','text':'```json\n'+json.dumps(value)+'\n```'}]}]}
    result=validate_explanation(response_text(response),RECORDS[:1])
    assert result.claims[0].evidence_ids==['flex']


def test_partial_provider_output_cannot_become_a_live_explanation():
    from flare.ai import response_text
    with pytest.raises(ValueError):
        response_text({'status':'incomplete','output_text':'{"claims":[]}'})


def test_only_final_phase_is_parsed_without_accepting_arbitrary_prose():
    from flare.ai import response_text
    body={'status':'completed', 'output_text':'aggregated text must be ignored', 'output':[
        {'type':'message','phase':'commentary','content':[{'type':'output_text','text':'Inspecting the dataset…'}]},
        {'type':'message','phase':'final_answer','content':[{'type':'output_text','text':'{"action":"finish"}'}]}]}
    assert response_text(body)=='{"action":"finish"}'
    body['output'].pop()
    with pytest.raises(ValueError):
        response_text(body)


def test_arabic_live_request_preserves_evidence_contract(monkeypatch):
    monkeypatch.setenv('AI_MODE','live')
    monkeypatch.setenv('KIE_API_KEY','test-key-never-sent')
    captured = {}
    async def post(self, *args, **kwargs):
        captured.update(kwargs['json'])
        result = {'claims':[{'text':'دليل محدود النطاق', 'evidence_ids':['flex'], 'classification':'Experimental evidence', 'limitations':['غير معاير']}], 'missing_information':[], 'abstain':True}
        return httpx.Response(200, json={'output_text':json.dumps(result), 'credits_consumed':0.09}, headers={'content-type':'application/json'}, request=httpx.Request('POST','https://example.test'))
    monkeypatch.setattr(httpx.AsyncClient, 'post', post)
    result = asyncio.run(explain(RECORDS[:1], 'ar'))
    assert result['mode'] == 'live'
    assert result['claims'][0]['text'] == 'دليل محدود النطاق'
    assert 'in Arabic' in captured['input'][0]['content'][0]['text']


def test_classification_cannot_be_upgraded_by_provider():
    from flare.ai import validate_explanation
    result = {'claims':[{'text':'A claim', 'evidence_ids':['flex'], 'classification':'Safety certification', 'limitations':[]}], 'missing_information':[], 'abstain':True}
    with pytest.raises(ValueError, match='classification'):
        validate_explanation(json.dumps(result), RECORDS[:1])
