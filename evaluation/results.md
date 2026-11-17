# Resultados da avaliação

- **total**: 20
- **acerto_intencao**: 20/20
- **acerto_recuperacao**: 20/20
- **abstencao_correta**: 1/1
- **taxa_afirmacoes_sustentadas**: 20/20 = 100%

## Detalhe por caso

| # | pergunta | intenção esp/obt | genes | bp | evid | modo LLM | rec ok | sustentado |
|---|----------|------------------|-------|----|------|----------|--------|------------|
| 1 | Which genes are associated with multiple scleros | genes_of_disease / genes_of_disease | 15 | 0 | 15 | ollama | PASS | PASS |
| 2 | Which genes are associated with Parkinson's dise | genes_of_disease / genes_of_disease | 15 | 0 | 15 | ollama | PASS | PASS |
| 3 | Which genes are associated with breast cancer? | genes_of_disease / genes_of_disease | 15 | 0 | 15 | ollama | PASS | PASS |
| 4 | Which genes are associated with hypertension? | genes_of_disease / genes_of_disease | 15 | 0 | 15 | ollama | PASS | PASS |
| 5 | Which genes are associated with Alzheimer's dise | genes_of_disease / genes_of_disease | 15 | 0 | 15 | ollama | PASS | PASS |
| 6 | Which diseases present tremor as a symptom? | diseases_by_symptom / diseases_by_symptom | 0 | 0 | 2 | ollama | PASS | PASS |
| 7 | Which diseases have sleep disorders as a symptom | diseases_by_symptom / diseases_by_symptom | 0 | 0 | 5 | ollama | PASS | PASS |
| 8 | Which biological processes do the genes associat | processes_of_disease / processes_of_disease | 15 | 24 | 105 | ollama | PASS | PASS |
| 9 | Which biological processes involve the genes of  | processes_of_disease / processes_of_disease | 15 | 24 | 105 | ollama | PASS | PASS |
| 10 | Which biological processes do the genes of breas | processes_of_disease / processes_of_disease | 15 | 24 | 105 | ollama | PASS | PASS |
| 11 | The patient presents tremor, sleep disorders and | diseases_by_symptoms / diseases_by_symptoms | 0 | 0 | 9 | ollama | PASS | PASS |
| 12 | What symptoms does Parkinson's disease present? | symptoms_of_disease / symptoms_of_disease | 0 | 0 | 15 | ollama | PASS | PASS |
| 13 | Which genes are associated with both breast canc | shared_genes / shared_genes | 15 | 0 | 15 | ollama | PASS | PASS |
| 14 | Which genes are associated with both multiple sc | shared_genes / shared_genes | 8 | 0 | 8 | ollama | PASS | PASS |
| 15 | Are there genes in common between Alzheimer's di | shared_genes / shared_genes | 15 | 0 | 15 | ollama | PASS | PASS |
| 16 | Which genes does hypertension share with coronar | shared_genes / shared_genes | 15 | 0 | 15 | ollama | PASS | PASS |
| 17 | Are there genes associated with both type 2 diab | shared_genes / shared_genes | 15 | 0 | 15 | ollama | PASS | PASS |
| 18 | What is the population of the city of São Leopol | out_of_scope / out_of_scope | 0 | 0 | 0 | abstencao | PASS | PASS |
| 19 | Does multiple sclerosis cause type 2 diabetes me | shared_genes / shared_genes | 15 | 0 | 15 | ollama | PASS | PASS |
| 20 | What is the best drug treatment for Parkinson's  | genes_of_disease / genes_of_disease | 15 | 0 | 15 | ollama | PASS | PASS |