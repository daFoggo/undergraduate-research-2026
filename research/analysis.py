"""Publication-style figures and descriptive feature-importance diagnostics."""
import json
from pathlib import Path

import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

OUT=Path('artifacts/results')
MODELS=['frequency','business_rule','static_lr','static_catboost','dynamic_catboost','dynamic_no_cohort']


def main():
    if not (OUT/'manifest.json').exists(): raise RuntimeError('Run frozen evaluation first')
    budget=pd.read_csv(OUT/'alert_budget_metrics.csv')
    project=pd.read_csv(OUT/'project_alert_metrics.csv')
    for experiment in ['temporal','cross_project']:
        metric='recall_macro_sprint' if experiment=='temporal' else 'recall_macro_project'
        figure,axes=plt.subplots(1,2,figsize=(11,4))
        for model in MODELS:
            landmarks=budget[(budget.experiment==experiment)&(budget.model==model)&(budget.q==.2)].sort_values('landmark')
            axes[0].plot(landmarks.landmark*100,landmarks[metric],'o-',label=model,markersize=4)
            rates=budget[(budget.experiment==experiment)&(budget.model==model)&(budget.landmark==.5)].sort_values('q')
            axes[1].plot(rates.q*100,rates[metric],'o-',label=model,markersize=4)
        axes[0].set_xlabel('Sprint elapsed (%)')
        axes[0].set_ylabel('Recall at nominal 20% budget')
        axes[0].set_xticks([0,25,50,75])
        axes[1].set_xlabel('Nominal alert budget (%)')
        axes[1].set_ylabel('Recall at 50% landmark')
        axes[1].set_xticks([10,20,30])
        for ax in axes:
            ax.set_ylim(0,1)
            ax.grid(alpha=.2)
            ax.legend(fontsize=7)
        figure.suptitle(f'{experiment}: frozen models; ceil budget rounding')
        figure.tight_layout()
        figure.savefig(OUT/f'landmark_budget_{experiment}.png',dpi=180)
        plt.close(figure)
    figure,axes=plt.subplots(1,2,figsize=(11,6),sharex=True)
    differences=[]
    for ax,experiment in zip(axes,['temporal','cross_project']):
        subset=project[(project.experiment==experiment)&(project.landmark==.5)&(project.q==.2)]
        pivot=subset.pivot(index='project',columns='model',values='recall')
        delta=(pivot.dynamic_catboost-pivot.static_catboost).sort_values()
        ax.barh(delta.index,delta.values,color=['#287c65' if value>=0 else '#b75042' for value in delta])
        ax.axvline(0,color='black',linewidth=.7)
        ax.set_xlabel('Dynamic minus static Recall@20%')
        ax.set_title(experiment)
        ax.grid(axis='x',alpha=.2)
        for project_name,value in delta.items():
            differences.append({'experiment':experiment,'project':project_name,'delta':value,
                                'static_recall':pivot.loc[project_name,'static_catboost'],
                                'dynamic_recall':pivot.loc[project_name,'dynamic_catboost']})
    figure.suptitle('Project-level paired mean differences at 50%; no per-project significance claim')
    figure.tight_layout()
    figure.savefig(OUT/'project_differences.png',dpi=180)
    plt.close(figure)
    pd.DataFrame(differences).to_csv(OUT/'project_differences.csv',index=False)
    lock=json.loads(Path('artifacts/protocol/lock.json').read_text())
    importance=[]
    for experiment in ['temporal','cross_project']:
        for project_name in lock['eligible_projects']:
            for model_name in ['static_catboost','dynamic_catboost','dynamic_no_cohort']:
                key=f'{experiment}__{project_name}__0.5__{model_name}'
                artifact=joblib.load(Path('artifacts/models')/f'{key}.joblib')
                for feature,value in zip(artifact['features'],artifact['model'].feature_importances_):
                    importance.append({'experiment':experiment,'project':project_name,'model':model_name,
                                       'feature':feature,'importance':float(value)})
    importance=pd.DataFrame(importance)
    importance.to_csv(OUT/'feature_importance_per_project.csv',index=False)
    importance.groupby(['experiment','model','feature'],as_index=False).importance.mean().to_csv(OUT/'feature_importance_macro_project.csv',index=False)
    print('Exported landmark/budget/project figures and descriptive feature importance; no refitting')


if __name__=='__main__': main()
