import type {Language} from './i18n';

export function datasetLabel(title:string,language:Language):string {
  const match=title.match(/^([A-Z0-9]+) — supplied experimental observations$/);
  if(!match)return title;
  const chamber=match[1].startsWith('C039');
  return (language==='ar'?(chamber?'قياسات حجرة التجربة':'قياسات ACME'):(chamber?'Chamber observations':'ACME observations'))+' · '+match[1];
}
