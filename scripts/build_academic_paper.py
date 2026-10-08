"""Convert the reviewed manuscript to standalone LaTeX with embedded vector figures.

No external bibliography or image files are needed by the LaTeX compiler.
"""
import csv
import argparse
import json
import re
from pathlib import Path

import pypandoc

ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT/'papers/sprint-risk'
SOURCE=PAPER/'source/manuscript.md'
TARGET=ROOT/'documents/Academic_paper_sprint_risk.tex'
KEYS={1:'tawosi2022tawos',2:'tawosv11',3:'tu2018careful',4:'teinemaa2019outcome',
      5:'prokhorenkova2018catboost',6:'bui2025agents',7:'sklearncalibration'}


def coordinates(filename,x,y):
    with (ROOT/'artifacts/results'/filename).open(encoding='utf-8',newline='') as handle:
        return ' '.join(f'({float(row[x]):.8f},{float(row[y]):.8f})' for row in csv.DictReader(handle))


def calibration_figure(experiment):
    parts=[r'\begin{figure}[htbp]',r'\centering',r'\begin{tikzpicture}',
           r'\begin{groupplot}[group style={group size=2 by 1,horizontal sep=1.2cm},width=0.45\textwidth,height=5.8cm,'
           r'xmin=0,xmax=1,ymin=0,ymax=1,xlabel={Predicted risk},ylabel={Observed non-completion},'
           r'tick label style={font=\scriptsize},label style={font=\small},title style={font=\small},'
           r'legend style={font=\scriptsize,at={(0.02,0.98)},anchor=north west},grid=major,grid style={gray!15}]']
    for score,title in [('p_raw','Raw'),('p','Validation sigmoid')]:
        parts.append(r'\nextgroupplot[title={'+title+'}]')
        parts.append(r'\addplot[gray,dashed,forget plot] coordinates {(0,0) (1,1)};')
        for model,label,color,mark in [('static_catboost','Static','blue','square*'),
                                       ('dynamic_catboost','Dynamic','orange','*'),
                                       ('dynamic_no_cohort','Dynamic w/o cohort','teal','triangle*')]:
            data=coordinates(f'calibration_bins__{experiment}__{model}__{score}.csv','prediction','observed')
            parts.append(r'\addplot[color='+color+',mark='+mark+r',mark size=1.7pt,thick] coordinates {'+data+'};')
            parts.append(r'\addlegendentry{'+label+'}')
    parts += [r'\end{groupplot}',r'\end{tikzpicture}',
              r'\caption{'+experiment.replace('_','-')+r' reliability at the midpoint. Ten fixed bins; bin counts and project-specific diagnostics are retained in the artifacts.}',
              r'\label{fig:calibration-'+experiment.replace('_','-')+'}',r'\end{figure}']
    return '\n'.join(parts)


def project_figure():
    with (ROOT/'artifacts/results/project_differences.csv').open(encoding='utf-8',newline='') as handle:
        records=list(csv.DictReader(handle))
    parts=[r'\begin{figure}[htbp]',r'\centering',r'\begin{tikzpicture}',
           r'\begin{groupplot}[group style={group size=2 by 1,horizontal sep=2.6cm},width=0.40\textwidth,height=7cm,'
           r'xmin=0,xmax=0.36,ymin=-0.8,ymax=13.8,xlabel={$\Delta$ Recall},tick label style={font=\scriptsize},'
           r'label style={font=\small},title style={font=\small},xmajorgrids,grid style={gray!15}]']
    for experiment,title in [('temporal','Temporal'),('cross_project','Cross-project')]:
        subset=sorted((row for row in records if row['experiment']==experiment),key=lambda row:float(row['delta']))
        labels=','.join(row['project'] for row in subset)
        ticks=','.join(str(i) for i in range(len(subset)))
        data=' '.join(f'({float(row["delta"]):.8f},{i})' for i,row in enumerate(subset))
        parts.append(r'\nextgroupplot[title={'+title+'},ytick={'+ticks+'},yticklabels={'+labels+'}]')
        parts.append(r'\addplot[xbar,bar width=6pt,fill=teal!80,draw=teal!80] coordinates {'+data+'};')
    parts += [r'\end{groupplot}',r'\end{tikzpicture}',
              r'\caption{Project-level dynamic--static differences at the midpoint. Bars are point estimates, not individual-project confidence intervals.}',
              r'\label{fig:projects}',r'\end{figure}']
    return '\n'.join(parts)


PREAMBLE=r'''\documentclass[11pt,a4paper]{article}
\usepackage[margin=24mm]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage{amsmath,amssymb}
\usepackage{booktabs,longtable,array,calc}
\usepackage{graphicx}
\usepackage{xurl}
\usepackage{hyperref}
\usepackage{pgfplots}
\usepgfplotslibrary{groupplots}
\pgfplotsset{compat=1.18}
\hypersetup{colorlinks=true,linkcolor=blue!50!black,citecolor=blue!50!black,urlcolor=blue!50!black}
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
\setlength{\emergencystretch}{3em}
\setlength{\parskip}{0.3em}
\title{Early Warning of Recorded Sprint Non-Completion:\\Execution Histories, Calibration, and Alert Budgets}
\author{Anonymous manuscript draft}
\date{8 October 2026}
\begin{document}
\maketitle
'''

BIBLIOGRAPHY=r'''\begin{thebibliography}{9}
\bibitem{tawosi2022tawos} V.~Tawosi, A.~Al-Subaihin, R.~Moussa, and F.~Sarro. A Versatile Dataset of Agile Open Source Software Projects. In \emph{MSR}, pp.~707--711, 2022. \url{https://doi.org/10.1145/3524842.3528029}.
\bibitem{tawosv11} SOLAR Group. \emph{The TAWOS Dataset, Version 1.1}. \url{https://github.com/SOLAR-group/TAWOS}; dataset DOI: \url{https://doi.org/10.5522/04/21308124}. Accessed 8 October 2026.
\bibitem{tu2018careful} F.~Tu, J.~Zhu, Q.~Zheng, and M.~Zhou. Be Careful of When: An Empirical Study on Time-Related Misuse of Issue Tracking Data. In \emph{ESEC/FSE}, 2018. \url{https://doi.org/10.1145/3236024.3236054}.
\bibitem{teinemaa2019outcome} I.~Teinemaa, M.~Dumas, M.~La~Rosa, and F.~M.~Maggi. Outcome-Oriented Predictive Process Monitoring: Review and Benchmark. \emph{ACM TKDD}, 13(2), 2019. \url{https://doi.org/10.1145/3301300}.
\bibitem{prokhorenkova2018catboost} L.~Prokhorenkova, G.~Gusev, A.~Vorobev, A.~V.~Dorogush, and A.~Gulin. CatBoost: Unbiased Boosting with Categorical Features. In \emph{NeurIPS}, vol.~31, 2018. \url{https://arxiv.org/abs/1706.09516}.
\bibitem{bui2025agents} T.-L.~Bui, H.~K.~Dam, and R.~Hoda. An LLM-based Multi-Agent Framework for Agile Effort Estimation. \emph{arXiv:2509.14483}, 2025. \url{https://arxiv.org/abs/2509.14483}.
\bibitem{sklearncalibration} scikit-learn developers. \emph{Probability Calibration}. \url{https://scikit-learn.org/stable/modules/calibration.html}. Accessed 8 October 2026; experimental version 1.9.1.
\end{thebibliography}
'''


def convert(text):
    text=text.replace(r'\\(', '$').replace(r'\\)', '$')
    expressions=['s','i','t_{0s}','t_{1s}','S_i(t)','t','t_{s,\\lambda}','R_s','d','u','C=1','C=10^6','n_s','TP_s/P_s','P_s>0','K_s']
    replacements={'('+value+')':'$'+value+'$' for value in expressions}
    pattern='|'.join(re.escape(value) for value in sorted(replacements,key=len,reverse=True))
    # Protect existing math, and replace prose delimiters in one pass (no nested rewrites).
    segments=re.split(r'(\\\[[\s\S]*?\\\]|\$[^$]*\$)',text)
    text=''.join(segment if index%2 else re.sub(pattern,lambda match:replacements[match.group(0)],segment)
                 for index,segment in enumerate(segments))
    text=text.replace('\u2212','-')
    text=re.sub(r'^(#{2,3})\s+(?:\d+\.)+\s+',r'\1 ',text,flags=re.MULTILINE)
    text=re.sub(r'\[(\d+(?:,\d+)*)\](?!\()',lambda match:r'\cite{'+','.join(KEYS[int(n)] for n in match.group(1).split(','))+'}',text)
    text=re.sub(r'\[([^\]]+)\]\(([^)]+\.md)\)',r'\1',text)
    text=text.replace('![Figure 1. Project-level differences at the midpoint. Bars are point estimates, not individual-project confidence intervals.](../artifacts/results/project_differences.png)',project_figure())
    text=text.replace('![Figure 2. Temporal reliability before and after validation-only sigmoid recalibration. Bin counts and project-level diagnostics are available in the artifact tables.](../artifacts/results/calibration_temporal.png)',calibration_figure('temporal')+'\n\n'+calibration_figure('cross_project'))
    result=pypandoc.convert_text(text,'latex',format='markdown+raw_tex+tex_math_dollars+tex_math_single_backslash',extra_args=['--number-sections','--shift-heading-level-by=-1','--wrap=none'])
    result=result.replace('\r\n','\n')
    result=re.sub(r'\\texttt\{([^}]+)\}',lambda match:r'\texttt{'+match.group(1).replace('/',r'/\allowbreak{}').replace(r'\_',r'\_\allowbreak{}')+'}',result)
    return result


def generate_from_markdown():
    source=SOURCE.read_text(encoding='utf-8')
    abstract=source.split('## Abstract\n',1)[1].split('**Keywords:**',1)[0].strip()
    keywords=source.split('**Keywords:**',1)[1].split('\n',1)[0].strip()
    main_text='## 1. Introduction'+source.split('## 1. Introduction',1)[1]
    body,remaining=main_text.split('## References',1)
    appendix='## Appendix A. Artifact Map'+remaining.split('## Appendix A. Artifact Map',1)[1]
    appendix=appendix.replace('Machine-readable entries are available in [references.bib](references.bib).','')
    latex=PREAMBLE+'\n\\begin{abstract}\n'+convert(abstract)+'\n\\end{abstract}\n'
    latex+=r'\noindent\textbf{Keywords:} '+convert(keywords)+'\n\n'+convert(body)
    latex+='\n'+BIBLIOGRAPHY+'\n\\appendix\n'+convert(appendix.replace('## Appendix A. Artifact Map','## Artifact Map'))+'\n\\end{document}\n'
    TARGET.write_text(latex,encoding='utf-8')
    assert r'\includegraphics' not in latex
    assert r'\bibliography{' not in latex
    assert latex.count(r'\begin{figure}')==3
    print(f'Generated standalone LaTeX: {TARGET}; 3 embedded vector figures; 7 references; Pandoc {pypandoc.get_pandoc_version()}')


def organize():
    if (PAPER/'main.tex').exists():
        raise RuntimeError('Modular paper already exists; use the default build to preserve section edits.')
    latex=TARGET.read_text(encoding='utf-8')
    for name in ['sections','figures','build']:
        (PAPER/name).mkdir(parents=True,exist_ok=True)
    preamble=latex.split('\\begin{document}',1)[0]
    class_line,preamble=preamble.split('\n',1)
    (PAPER/'preamble.tex').write_text(preamble,encoding='utf-8')
    body=latex.split('\\maketitle',1)[1].split('\\begin{thebibliography}',1)[0]
    chunks=re.split(r'(?=\\section\{)',body)
    names=['00_abstract','01_introduction','02_related_work','03_research_questions','04_data',
           '05_methods','06_results','07_discussion','08_validity','09_reproducibility','10_conclusion']
    assert len(chunks)==len(names),(len(chunks),len(names))
    for name,chunk in zip(names,chunks):
        for figure_index,figure in enumerate(re.findall(r'\\begin\{figure\}[\s\S]*?\\end\{figure\}',chunk)):
            label=re.search(r'\\label\{fig:([^}]+)\}',figure).group(1)
            filename='fig_'+label.replace('-','_')+'.tex'
            (PAPER/'figures'/filename).write_text(figure+'\n',encoding='utf-8')
            chunk=chunk.replace(figure,r'\input{figures/'+filename[:-4]+'}')
        (PAPER/'sections'/f'{name}.tex').write_text(chunk.strip()+'\n',encoding='utf-8')
    bibliography=r'\begin{thebibliography}'+latex.split(r'\begin{thebibliography}',1)[1].split(r'\end{thebibliography}',1)[0]+r'\end{thebibliography}'
    (PAPER/'bibliography.tex').write_text(bibliography+'\n',encoding='utf-8')
    appendix=latex.split(r'\appendix',1)[1].split(r'\end{document}',1)[0]
    (PAPER/'sections/11_artifact_map.tex').write_text(appendix.strip()+'\n',encoding='utf-8')
    main_text=class_line+'\n'+r'\input{preamble}'+'\n'+r'\begin{document}'+'\n'+r'\maketitle'+'\n'
    main_text+='\n'.join(r'\input{sections/'+name+'}' for name in names)+'\n'
    main_text+=r'\input{bibliography}'+'\n'+r'\appendix'+'\n'+r'\input{sections/11_artifact_map}'+'\n'+r'\end{document}'+'\n'
    (PAPER/'main.tex').write_text(main_text,encoding='utf-8')
    (PAPER/'references.bib').write_text((ROOT/'documents/references.bib').read_text(encoding='utf-8'),encoding='utf-8')


def flatten():
    dependencies=[]
    def expand(path,stack=()):
        path=path.resolve()
        if not path.is_relative_to(PAPER.resolve()): raise RuntimeError('Input outside paper folder')
        if path in stack: raise RuntimeError('Circular input')
        dependencies.append(path)
        source=path.read_text(encoding='utf-8')
        def include(match):
            relative=match.group(1)
            target=PAPER/relative
            if target.suffix!='.tex': target=target.with_suffix('.tex')
            return '% Source: '+str(target.relative_to(PAPER)).replace('\\','/')+'\n'+expand(target,stack+(path,))
        return re.sub(r'\\input\{([^}]+)\}',include,source)
    latex='% Generated preview. Edit papers/sprint-risk/sections and rebuild.\n'+expand(PAPER/'main.tex')
    assert r'\includegraphics' not in latex and r'\input{' not in latex
    assert latex.count(r'\begin{figure}')==3
    TARGET.write_text(latex,encoding='utf-8')
    (PAPER/'build').mkdir(exist_ok=True)
    (PAPER/'build/manuscript.tex').write_text(latex,encoding='utf-8')
    print(f'Flattened {len(dependencies)} LaTeX source files; current editor preview updated in place.')


def update_bibliography():
    entries=json.loads(pypandoc.convert_file(str(PAPER/'references.bib'),'csljson',format='bibtex'))
    entries={entry['id']:entry for entry in entries}
    def tex(value):
        replacements={'&':r'\&','%':r'\%','_':r'\_','#':r'\#','$':r'\$'}
        return ''.join(replacements.get(character,character) for character in str(value))
    lines=['% Generated from references.bib; edit that file, then rebuild.',r'\begin{thebibliography}{9}']
    for key in KEYS.values():
        entry=entries[key]
        authors=[]
        for author in entry.get('author',[]):
            authors.append(author.get('literal') or ' '.join(filter(None,[author.get('given'),author.get('family')])))
        parts=[tex('; '.join(authors))+'.',r'\emph{'+tex(entry['title'])+'}.']
        if entry.get('container-title'): parts.append(tex(entry['container-title'])+'.')
        if entry.get('volume'): parts.append('Vol.~'+tex(entry['volume'])+(('('+tex(entry['issue'])+')') if entry.get('issue') else '')+'.')
        if entry.get('page'): parts.append('pp.~'+tex(entry['page']).replace('-', '--')+'.')
        dates=entry.get('issued',{}).get('date-parts',[])
        if dates and dates[0]: parts.append(str(dates[0][0])+'.')
        url='https://doi.org/'+entry['DOI'] if entry.get('DOI') else entry.get('URL')
        if url: parts.append(r'\url{'+url+'}.')
        if entry.get('note'): parts.append(tex(entry['note'])+'.')
        lines.append(r'\bibitem{'+key+'} '+' '.join(parts))
    lines.append(r'\end{thebibliography}')
    (PAPER/'bibliography.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--organize',action='store_true',help='Initialize modular project once from the Markdown draft')
    parser.add_argument('--format-tables',action='store_true',help='Split and format the six draft tables once')
    args=parser.parse_args()
    if args.organize:
        generate_from_markdown()
        organize()
    if args.format_tables:
        organize_tables()
    update_bibliography()
    flatten()


def organize_tables():
    directory=PAPER/'tables'
    if directory.exists(): raise RuntimeError('Tables already split; edit table sources directly.')
    directory.mkdir()
    source=SOURCE.read_text(encoding='utf-8')
    blocks=re.findall(r'^\|[^\n]+\|(?:\n\|[^\n]*\|)+',source,re.MULTILINE)
    assert len(blocks)==6,len(blocks)
    specs=[('01_cohort','04_data','lrrr','Source, reconstructed, and evaluation populations. The source row counts issues, not issue--sprint instances.'),
           ('feature_groups','04_data',r'p{0.20\linewidth}p{0.74\linewidth}',None),
           ('02_performance','06_results','lrrrrrr',r'Midpoint results under upward-rounded nominal 20\% budgets. Temporal recall and precision are sprint-macro; cross-project recall and precision are project-macro. False alerts are mean counts per sprint.'),
           ('03_sensitivity','06_results','lrr',r'Dynamic--static differences at 50\%, in percentage points, with 95\% intervals. Only the first temporal contrast is the primary H1 test.'),
           ('04_probability','06_results','llrrr','Midpoint probability results. AP is averaged equally over projects; Brier is pooled over instances.'),
           ('artifact_map','11_artifact_map',r'p{0.28\linewidth}p{0.66\linewidth}','Local artifact map. Paths are relative to the repository root.')]
    for block,(name,section,columns,caption) in zip(blocks,specs):
        parsed=[[cell.strip() for cell in line.strip().strip('|').split('|')] for line in block.splitlines()]
        header,rows=parsed[0],parsed[2:]
        def cell(value):
            return convert(value).strip()
        headers=[cell(value) for value in header]
        if name=='01_cohort':
            headers=['Population / partition','Projects','Sprints','Issues / instances']
            rows[0][-1]='458,232 issues'
        if name=='02_performance':
            headers=['Method',r'\shortstack{Temporal\\recall (\%)}',r'\shortstack{Temporal\\precision (\%)}',
                     r'\shortstack{Temporal\\false alerts}',r'\shortstack{Cross-project\\recall (\%)}',
                     r'\shortstack{Cross-project\\precision (\%)}',r'\shortstack{Cross-project\\false alerts}']
            rows[-1][0]='Dynamic w/o cohort'
        if name=='03_sensitivity':
            headers=['Analysis',r'\shortstack{Temporal $\Delta$\\(95\% CI)}',r'\shortstack{Cross-project $\Delta$\\(95\% CI)}']
        if name=='04_probability':
            headers=['Setting','Model',r'\shortstack{AP macro\\project}',r'Raw Brier',r'\shortstack{Recalibrated\\Brier}']
        rendered=[' & '.join(headers)+r' \\',r'\midrule']
        rendered+=[' & '.join(cell(value) for value in row)+r' \\' for row in rows]
        body=r'\toprule'+'\n'+'\n'.join(rendered)+'\n'+r'\bottomrule'
        if name=='artifact_map':
            table=r'\begin{longtable}{@{}'+columns+r'@{}}'+'\n'+r'\caption{'+caption+r'}\label{tab:'+name+r'}\\'+'\n'+body+'\n'+r'\end{longtable}'
        else:
            table=r'\begin{table}[htbp]'+'\n'+r'\centering\footnotesize\setlength{\tabcolsep}{4pt}'+'\n'
            if caption: table+=r'\caption{'+caption+r'}\label{tab:'+name+'}'+'\n'
            table+=r'\begin{tabular}{@{}'+columns+r'@{}}'+'\n'+body+'\n'+r'\end{tabular}'+'\n'+r'\end{table}'
        (directory/f'{name}.tex').write_text(table+'\n',encoding='utf-8')
        path=PAPER/'sections'/f'{section}.tex'
        contents=path.read_text(encoding='utf-8')
        contents=contents.replace(r'\def\LTcaptype{none}',r'\def\LTcaptype{table}')
        contents=re.sub(r'\\textbf\{Table [1-4]\.[^\n]*\}\n\n','',contents)
        contents,count=re.subn(r'\\begin\{longtable\}[\s\S]*?\\end\{longtable\}',lambda match:r'\input{tables/'+name+'}',contents,count=1)
        assert count==1,(name,count)
        path.write_text(contents,encoding='utf-8')


if __name__=='__main__': main()
