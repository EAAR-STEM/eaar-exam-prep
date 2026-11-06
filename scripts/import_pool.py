#!/usr/bin/env python3
"""Convert official NCVEC DOCX/PDF/TXT documents to validated EAAR pool JSON.

Designed for administrator-initiated GitHub Actions. Never silently import partial files.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from datetime import date
from collections import Counter

CLASS_INFO={'technician':('T',35,300),'general':('G',35,300),'extra':('E',50,450)}
QUESTION=re.compile(r'^\s*([TGE]\d[A-Z]\d{2})\s*\(([A-D])\)\s*(\[[^\]]+\])?\s*(.*)$',re.I)
OPTION=re.compile(r'^\s*([A-D])\s*[.)]\s+(.+)$',re.I)
FIGURE=re.compile(r'\bfigure\s+([TGE]\d?[-–]\d+)\b',re.I)
WITHDRAWN=re.compile(r'\b([TGE]\d[A-Z]\d{2})\s*[-–—:]?\s*(?:(?:question\s+)?(?:withdrawn|deleted)|removed\s+from\s+use)\b',re.I)
MONTHS={m.lower():str(i).zfill(2) for i,m in enumerate(('January','February','March','April','May','June','July','August','September','October','November','December'),1)}
REVISION=re.compile(r'(?:errata\s+(?:issued|dated|revision)?\s*|revised\s*|updated\s*)(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(20\d{2})',re.I)

def read_document(path:Path)->str:
    suffix=path.suffix.lower()
    if suffix in ('.txt','.text'):
        return path.read_text(encoding='utf-8-sig')
    if suffix=='.docx':
        from docx import Document
        doc=Document(str(path))
        # Iterate XML paragraphs in document order, including paragraphs inside tables.
        ns='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        paragraphs=[]
        for p in doc.element.body.iter(ns+'p'):
            chunks=[]
            for node in p.iter():
                if node.tag==ns+'t':chunks.append(node.text or '')
                elif node.tag==ns+'tab':chunks.append(' ')
                elif node.tag==ns+'br':chunks.append('\n')
            paragraphs.append(''.join(chunks))
        return '\n'.join(paragraphs)
    if suffix=='.pdf':
        import fitz
        doc=fitz.open(str(path))
        text='\n'.join(p.get_text('text',sort=True) for p in doc)
        if len(text.strip())<5000:raise ValueError('PDF has little extractable text. Scanned/image PDFs require OCR or the official DOCX version; no inaccurate OCR import was attempted.')
        return text
    raise ValueError('Supported formats: .json, .txt, .docx, .pdf')

def compact(s:str)->str:
    return re.sub(r'\s+',' ',s).strip()

def parse(text:str):
    found=[]; incomplete=[]
    lines=text.replace('\r\n','\n').replace('\r','\n').replace('\u00a0',' ').split('\n')
    current=None;choice=-1
    def flush():
        nonlocal current,choice
        if current is None:return
        current['question']=compact(current['question'])
        current['answers']=[compact(v) for v in current['answers']]
        if len(current['answers'])==4 and all(current['answers']) and len(current['question'])>=6:
            m=FIGURE.search(current['question'])
            if m:current['figure']='figure-'+m[1].lower().replace('–','-')+'.png'
            found.append(current)
        else:incomplete.append(current['id'])
        current=None;choice=-1
    for line in lines:
        m=QUESTION.match(line)
        if m:
            flush();ident=m[1].upper()
            current={'id':ident,'group':ident[:3],'section':ident[:2],'question':m[4] or '',
                     'answers':[],'correct':'ABCD'.index(m[2].upper()),'refs':m[3] or '',
                     'note':'','figure':''}
            continue
        if current is None:continue
        m=OPTION.match(line)
        if m:
            n='ABCD'.index(m[1].upper())
            if n==len(current['answers']):
                current['answers'].append(m[2]);choice=n;continue
            if n==0:
                current['answers']=[m[2]];choice=0;continue
        if not line.strip():continue
        if choice<0:current['question']+=' '+line.strip()
        elif choice<len(current['answers']):current['answers'][choice]+=' '+line.strip()
    flush()
    withdrawn={m[1].upper() for m in WITHDRAWN.finditer(text)}
    found=[q for q in found if q['id'] not in withdrawn and not re.match(r'(withdrawn|deleted|removed from use)\b',q['question'],re.I)]
    return found,incomplete,withdrawn

def infer_meta(text:str,filename:str,klass:str):
    header=filename+'\n'+text[:8500]
    year=re.search(r'(20\d{2})\s*[-–—]\s*(20\d{2})',header)
    period=(year[1]+'–'+year[2]) if year else ''
    rev=REVISION.search(header)
    rev_date=rev[3]+'-'+MONTHS[rev[1].lower()]+'-'+rev[2].zfill(2) if rev else ''
    return {'years':period,'effectiveFrom':year[1]+'-07-01' if year else '',
            'effectiveTo':year[2]+'-06-30' if year else '',
            'poolUpdated':rev_date,'version':rev_date or period,
            'source':'NCVEC '+klass.capitalize()+' Question Pool (imported from '+filename+')'}

def validate(bank,klass,old):
    letter,expected_groups,minimum=CLASS_INFO[klass]
    questions=bank['questions']
    if not minimum<=len(questions)<=1200:raise ValueError(f'Only {len(questions)} questions parsed: expected >= {minimum}; refusing partial import.')
    seen=set()
    for q in questions:
        ident=q['id']
        if not re.fullmatch(fr'{letter}\d[A-Z]\d{{2}}',ident):raise ValueError(f'Wrong class or invalid ID {ident}')
        if ident in seen:raise ValueError(f'Duplicate question ID {ident}')
        seen.add(ident)
        if len(q['answers'])!=4 or not all(q['answers']):raise ValueError(f'Missing choices for {ident}')
        if not 0<=q['correct']<4:raise ValueError(f'Incorrect answer key for {ident}')
        if len(q['question'])<6:raise ValueError(f'Missing question text for {ident}')
    count=len({q['group'] for q in questions})
    if count!=expected_groups:raise ValueError(f'Only {count} question groups parsed; {expected_groups} required for exam selection. Aborting.')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',bank['effectiveFrom']):raise ValueError('Provide a valid --effective-from date (YYYY-MM-DD).')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',bank['effectiveTo']):raise ValueError('Provide a valid --effective-to date (YYYY-MM-DD).')
    for field in ('effectiveFrom','effectiveTo'):date.fromisoformat(bank[field])
    if bank['effectiveFrom']>bank['effectiveTo']:raise ValueError('Effective end precedes start.')
    if not bank['version'] or len(bank['version'])>80:raise ValueError('Missing or invalid pool version.')
    if not bank['years']:raise ValueError('Missing pool-year interval.')
    if bank['poolUpdated']:date.fromisoformat(bank['poolUpdated'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--class',dest='klass',choices=CLASS_INFO,required=True)
    parser.add_argument('--source',required=True,type=Path)
    parser.add_argument('--output',type=Path,help='Defaults to pools/<class>.json')
    parser.add_argument('--version',default='')
    parser.add_argument('--years',default='')
    parser.add_argument('--effective-from',default='')
    parser.add_argument('--effective-to',default='')
    parser.add_argument('--revision-date',default='')
    opts=parser.parse_args()
    source=opts.source.resolve();repo=Path(__file__).resolve().parents[1]
    if not source.exists():parser.error('Source file does not exist: '+str(source))
    output=opts.output or (repo/'pools'/(opts.klass+'.json'))
    old=json.loads(output.read_text()) if output.exists() else {'groupTitles':{}}
    if source.suffix.lower()=='.json':
        imported=json.loads(source.read_text(encoding='utf-8-sig'))
        if isinstance(imported,list):imported={'questions':imported}
        questions=imported.get('questions')
        if not isinstance(questions,list):raise ValueError('Expected JSON object with questions array')
        inferred={k:imported.get(k,'') for k in ('years','effectiveFrom','effectiveTo','poolUpdated','version','source')}
        incomplete=[];withdrawn=set()
    else:
        text=read_document(source)
        questions,incomplete,withdrawn=parse(text)
        inferred=infer_meta(text,source.name,opts.klass)
        imported={}
    # Dates and versions from this release take priority over those installed before it.
    bank={
        'licenseClass':opts.klass,
        'questions':questions,
        'groupTitles':{},
        'source':inferred.get('source') or 'Official NCVEC question pool',
        'version':opts.version or inferred.get('version') or '',
        'years':opts.years or inferred.get('years') or '',
        'effectiveFrom':opts.effective_from or inferred.get('effectiveFrom') or '',
        'effectiveTo':opts.effective_to or inferred.get('effectiveTo') or '',
        'poolUpdated':opts.revision_date or inferred.get('poolUpdated') or '',
        'publishedBy':'NCVEC Question Pool Committee',
        'official':True,'offline':True,'count':len(questions),
    }
    group_titles={**old.get('groupTitles',{}),**imported.get('groupTitles',{})}
    for group in sorted({q['group'] for q in questions}):bank['groupTitles'][group]=group_titles.get(group,group)
    validate(bank,opts.klass,old)
    missing_figures={q['figure'] for q in questions if q['figure'] and not (repo/'figures'/q['figure']).is_file()}
    if missing_figures:raise ValueError('Missing reference figure PNG files in figures/: '+', '.join(sorted(missing_figures)))
    known={q['id']:q for q in old.get('questions',[])}
    added=set(q['id'] for q in questions)-set(known)
    removed=set(known)-set(q['id'] for q in questions)
    modified=[q['id'] for q in questions if q['id'] in known and any(q.get(f)!=known[q['id']].get(f) for f in ('question','answers','correct','refs','figure','note'))]
    print('Class:',opts.klass,' Pool:',bank['years'],' Version:',bank['version'])
    print('Questions:',len(questions),' Groups:',len(bank['groupTitles']))
    print('Added:',len(added),'Modified:',len(modified),'Removed:',len(removed))
    print('Incompletely parsed records:',len(incomplete),'Withdrawn/Deleted references:',len(withdrawn))
    if incomplete:
        print('Incomplete IDs:',', '.join(incomplete[:50]))
        # Incomplete entries might be release notices, but block any suspicious loss.
        if len(incomplete)>10:raise ValueError('Too many incomplete question records. Do not publish without fixing the parser/source.')
    print('Removed IDs:',', '.join(sorted(removed)) if removed else '(none)')
    # A substantial drop could be extraction failure; reject even if absolute question count meets minimum.
    if old.get('questions') and len(questions)<len(old['questions'])*.85:
        raise ValueError('New pool is more than 15% smaller than the old one. Review source before publishing.')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(bank,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Wrote:',output)

if __name__=='__main__':main()
