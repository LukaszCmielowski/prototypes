# Tabular Foundation Models Comparison

## Overview
AutoGluon 1.5.1 integrates three cutting-edge foundational tabular models that leverage pre-training and in-context learning for structured data prediction.

## Detailed Comparison Table

| Feature | Mitra | TabICL | TabPFNv2 |
|---------|-------|--------|----------|
| **Architecture** | In-context learning with synthetic pre-training | Transformer-based in-context learning | Prior-Fitted Networks |
| **Optimal Dataset Size** | < 5,000 samples and < 100 features | Large tabular datasets | < 10,000 samples |
| **Training Paradigm** | Pre-trained on synthetic data with diverse synthetic priors | Pre-trained checkpoints from Hugging Face | Prior knowledge encoded in network architecture |
| **Learning Modes** | Zero-shot + Fine-tuning | In-context learning | Prior-fitted (embedded inductive biases) |
| **Task Support** | Classification & Regression | Classification | Classification & Regression |
| **Hardware Support** | GPU & CPU | GPU (typical for transformers) | GPU & CPU |
| **Fine-tuning** | ✅ Yes (with `fine_tune` parameter) | ⚠️ Limited (designed for ICL) | ❌ No (uses architectural priors) |
| **Key Hyperparameters** | `fine_tune`, `fine_tune_steps` | Context window, checkpoint version | Dataset-specific priors |
| **Performance Highlights** | SOTA on TabRepo, TabZilla, AMLB, TabArena benchmarks | 97% validation accuracy (Wine dataset) | Accurate predictions through architectural optimization |
| **Unique Advantage** | Privacy-preserving (synthetic pre-training) | Leverages contextual examples from related data | Architectural inductive biases for small data |
| **Best Use Cases** | Small-medium datasets, enterprise with data privacy concerns | Limited training data with available context | Small datasets requiring quick, accurate predictions |
| **Installation** | Included in AutoGluon base | `pip install autogluon.tabular[tabicl]` | Included (requires `REALTABPFN-V2` model name) |
| **Checkpoint Source** | AutoGluon proprietary | Hugging Face (`tabicl-classifier-v2-20260212.ckpt`) | Bundled with AutoGluon |
| **License** | Apache-2.0 | Open-source | Open-source |
| **Paper Reference** | AutoGluon documentation | Qu et al. - "TabICL: A Tabular Foundation Model for In-Context Learning on Large Data" | Hollmann et al. - "Accurate predictions on small data with a tabular foundation model" (Nature) |

## Performance Benchmarks

| Benchmark | Mitra | TabICL | TabPFNv2 |
|-----------|-------|--------|----------|
| **TabRepo** | ⭐ State-of-the-art | Not specified | Good for small subsets |
| **TabZilla** | ⭐ State-of-the-art | Not specified | Good for small subsets |
| **AMLB** | ⭐ State-of-the-art | Not specified | Not specified |
| **TabArena** | ⭐ State-of-the-art | Not specified | Not specified |
| **Small Datasets** | ⭐ Excels (< 5k samples) | Moderate | ⭐ Optimized (< 10k samples) |
| **Large Datasets** | Moderate | ⭐ Designed for large data | Not recommended |

## Architecture Comparison

### Mitra
- **Type**: Proprietary in-context learning model
- **Pre-training**: Synthetic data with diverse priors
- **Strength**: Breadth of synthetic training coverage
- **Innovation**: Privacy-preserving synthetic-only pre-training

### TabICL
- **Type**: Transformer-based
- **Pre-training**: Real-world tabular data (via Hugging Face)
- **Strength**: Contextual example utilization
- **Innovation**: In-context learning for tabular data

### TabPFNv2
- **Type**: Prior-Fitted Networks
- **Pre-training**: Architectural encoding of domain knowledge
- **Strength**: Embedded inductive biases
- **Innovation**: Accuracy through architecture, not scale

## Selection Guide

### Choose Mitra when:
- Working with small to medium datasets (< 5,000 samples)
- Data privacy is critical (benefits from synthetic pre-training)
- Need both zero-shot and fine-tuning capabilities
- Require support for both classification and regression
- Want state-of-the-art performance on standard benchmarks

### Choose TabICL when:
- Working with large tabular datasets
- Have limited training data but access to related contextual examples
- Need strong performance with in-context learning
- Can leverage transformer infrastructure
- Primary focus is classification tasks

### Choose TabPFNv2 when:
- Working with small datasets (< 10,000 samples)
- Need quick, accurate predictions without extensive training
- Want to leverage architectural inductive biases
- Prefer models optimized for efficiency over scale
- Looking for peer-reviewed approach (Nature publication)

## Integration Example

```python
from autogluon.tabular import TabularPredictor

# Using Mitra (zero-shot)
predictor = TabularPredictor(label='target').fit(
    train_data,
    hyperparameters={'MITRA': {}}
)

# Using Mitra (with fine-tuning)
predictor = TabularPredictor(label='target').fit(
    train_data,
    hyperparameters={'MITRA': {'fine_tune': True, 'fine_tune_steps': 100}}
)

# Using TabICL
predictor = TabularPredictor(label='target').fit(
    train_data,
    hyperparameters={'TABICL': {}}
)

# Using TabPFNv2
predictor = TabularPredictor(label='target').fit(
    train_data,
    hyperparameters={'REALTABPFN-V2': {}}
)
```

## Summary

All three models represent different approaches to tabular foundation models:

- **Mitra**: Synthetic pre-training for privacy and generalization
- **TabICL**: Transformer-based in-context learning for large datasets
- **TabPFNv2**: Architectural optimization for small data efficiency

The choice depends on dataset size, privacy requirements, and whether you need zero-shot, in-context learning, or architectural optimization capabilities.
