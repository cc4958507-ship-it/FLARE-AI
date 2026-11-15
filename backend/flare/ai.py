"""Server-only evidence explanations. The language model has no state authority."""
import json
import os
import httpx
from pydantic import BaseModel, ConfigDict, Field
from .provider import request_model, ProviderError


class Claim(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str = Field(max_length=3000)
    evidence_ids: list[str]
    classification: str
    limitations: list[str]


class Explanation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    claims: list[Claim] = Field(max_length=3)
    missing_information: list[str]
    abstain: bool


def response_text(body):
    """Read message output only; reasoning items are not evidence explanations."""
    if body.get('error') or (body.get('code') is not None and body['code'] not in (0, 200, '200')):
        raise ValueError('Provider returned an error')
    if body.get('status') in ('failed', 'incomplete', 'cancelled'):
        raise ValueError('Provider response did not complete')
    items = [item for item in body.get('output') or [] if isinstance(item, dict) and item.get('type') == 'message']
    phased = any(item.get('phase') for item in items)
    if phased:
        items = [item for item in items if item.get('phase') == 'final_answer']
        if not items:
            raise ValueError('No final answer message')
    if not phased and isinstance(body.get('output_text'), str):
        return body['output_text']
    parts=[]
    for item in items:
        if not isinstance(item, dict) or item.get('type') != 'message':
            continue
        for content in item.get('content') or []:
            if isinstance(content,dict) and content.get('type') == 'output_text' and isinstance(content.get('text'),str):
                parts.append(content['text'])
    if not parts:
        raise ValueError('No completed message text in provider response')
    return ''.join(parts)


def validate_explanation(text, evidence):
    text=text.strip()
    # Some Responses-compatible providers wrap JSON in a single Markdown fence.
    # Only that exact wrapper is accepted; prose or trailing output still fails.
    if text.startswith('```json\n') and text.endswith('\n```'):
        text=text[len('```json\n'):-len('\n```')]
    result=Explanation.model_validate_json(text)
    allowed={e['id'] for e in evidence}
    for claim in result.claims:
        if not claim.evidence_ids or not set(claim.evidence_ids) <= allowed:
            raise ValueError('Unknown evidence reference')
        classifications = {e['classification'] for e in evidence if e['id'] in claim.evidence_ids}
        if claim.classification not in classifications:
            raise ValueError('Claim classification does not match cited evidence')
    return result


async def explain(evidence, language='en'):
    fallback = {
        'mode':'offline',
        'message':'Reviewed source summaries; no live model request.',
        'claims':[{'text':e['finding'],'evidence_ids':[e['id']],'classification':e['classification'],'limitations':e['unknowns']} for e in evidence],
        'missing_information':sorted({u for e in evidence for u in e['unknowns']}),
        'abstain':True,
    }
    if os.getenv('AI_MODE','offline') != 'live' or not os.getenv('KIE_API_KEY'):
        return fallback
    example={'claims':[{'text':'A brief evidence-grounded explanation.','evidence_ids':[evidence[0]['id']],'classification':evidence[0]['classification'],'limitations':['Use the actual source limitations.']}],'missing_information':[],'abstain':True}
    prompt=(
        'Explain only the supplied evidence. Return ONE JSON object with exactly the keys and value types in this example. '
        'Use at most three brief claims. Do not include Markdown or any prose outside JSON. '
        'Cite only evidence IDs from the supplied records. Preserve their evidence classification and limitations. '
        'Do not calculate combustion status, invent measurements, or give equipment instructions. '+
        ('Write the claim text, limitations and missing information in Arabic. Keep evidence IDs and classification strings unchanged. ' if language == 'ar' else 'Write in English. ')+
        'The example is a shape, not content to repeat. Example: '+json.dumps(example)+
        '\nEvidence: '+json.dumps(evidence)
    )
    try:
        body=await request_model(prompt, purpose='evidence_explanation')
        result=validate_explanation(response_text(body),evidence)
        return {'mode':'live','message':'Kie evidence explanation; deterministic rules remain independent.',
                'model':body.get('model'), 'usage':body.get('usage'),
                'credits_consumed':body.get('credits_consumed'),
                'response_id':body.get('id'), **result.model_dump()}
    except (ProviderError,httpx.HTTPError,ValueError,KeyError,TypeError,AttributeError) as exc:
        return {**fallback,'mode':'unavailable','error_code':exc.code if isinstance(exc,ProviderError) else 'INVALID_PROVIDER_OUTPUT',
                'message':'AI unavailable. Showing reviewed source summaries. No automatic paid retry.'}
