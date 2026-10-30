# How I would improve Écopoétique Task 2 beyond 71.2% accuracy

Your current pipeline is already at a point where **the next major improvement is more likely to come from changing how the problem is represented and learned than from replacing Qwen3-30B with another LLM or endlessly refining the prompt.**

Given what you have tested, I would focus on six areas:

1. **Reformulate the 12-category decision as a set of explicit linguistic decisions.**
2. **Give the classifier more of the literary context, not just the sentence.**
3. **Use contrastive examples retrieved from your annotated data.**
4. **Benchmark supervised classifiers, including CamemBERT, against the LLM.**
5. **Investigate whether the nominal-metaphor category is genuinely distinguishable under the annotation guidelines.**
6. **Use targeted annotation to improve the training data, rather than simply collecting more random examples.**

There are also some improvements you can make to the evaluation itself, which will help you establish whether a technique genuinely improves performance.

I'll explain each approach in the context of your existing hybrid pipeline, rather than treating this as a generic text-classification problem.

## 1. First, understand what the 71.2% result actually tells you

Your current result is:

| Measurement | Result |
|---|---:|
| Gold-standard examples | 184 |
| Correct predictions | 131 |
| Incorrect predictions | 53 |
| Accuracy | 71.2% |

The important observation is that your nominal-metaphor errors are distributed across several other categories, rather than being concentrated in a single confusion pair.

That pattern raises three possibilities.

**Possibility A: The model is missing an underlying linguistic feature.**

For instance, it may recognise that an expression is figurative but fail to distinguish between identity, qualification, comparison and other structural relationships consistently.

**Possibility B: The categories have overlapping definitions.**

A single expression might satisfy the grammatical description of one category while also exhibiting the rhetorical properties of another. If the annotation guidelines do not specify which label takes precedence, the model has no reliable decision boundary to learn.

**Possibility C: The model lacks sufficient context.**

A sentence may not contain enough information to establish what the animal or plant expression refers to, whether the expression is conventionalised, or how it relates to the surrounding description.

These possibilities require different solutions. Adding more prompt instructions will not necessarily help if the underlying categories overlap or the available context is insufficient.

### One important evaluation consideration

With 184 examples, your observed accuracy also has considerable statistical uncertainty. Under a simple independent-binomial assumption, a 95% confidence interval for 131/184 is approximately **64.3%–77.3%**. If examples from the same novel are correlated, a properly grouped estimate could be less precise.

There is another point worth checking: you mentioned that you refined the prompt by examining misclassified examples. If those examples came from the same 184-item gold set, that set has also served as a development set. The 71.2% remains a valid description of performance on those examples, but it is no longer a completely independent estimate of performance on unseen data.

This does not mean the result was deliberately inflated. It is a normal consequence of iterative model development.

For a defensible final evaluation, keep a genuinely untouched test set or use an evaluation design that accounts for repeated experimentation.

I would also report macro-F1, per-category precision and recall, and a confusion matrix alongside accuracy. This is especially important for a 12-category classification problem, where the most frequent category can dominate the overall accuracy.

With that foundation in place, here are the improvements I would investigate.

---

## 2. Highest-priority idea: Decompose rhetorical classification into explicit linguistic decisions

**This is the first architectural change I would investigate.**

Your current approach asks Qwen3 to work through several reasoning steps:

- Identify the animal or plant expression.
- Identify what it describes.
- Identify the shared property.
- Determine whether the source and target are different things.
- Assign one of the 12 rhetorical categories.

That is a sensible approach, and your results suggest it is better than direct classification.

However, it still asks the model to perform two fundamentally different jobs at once:

1. Recover the linguistic structure of the expression.
2. Map that structure onto the researcher's rhetorical taxonomy.

The model can successfully identify a metaphor and its target but still assign the wrong category.

### My proposal: Use an intermediate linguistic representation

Instead of having the model directly generate a final category from its reasoning, make it identify a small set of explicit, observable features first.

For example, consider:

> Cet homme est un véritable loup.

A possible intermediate representation would look like this:

```json
{
  "target_expression": "loup",
  "target_referent": "cet homme",
  "figurative_source": "loup",
  "explicit_comparison_marker": false,
  "predicative_or_identity_relation": true,
  "fixed_expression": false,
  "target_is_literal_animal": false,
  "evidence_span": "Cet homme est un véritable loup"
}
```

These are illustrative feature values, not a claim that the passage's rhetorical classification is settled by this JSON alone.

The classifier would then map the extracted features to a category according to the researcher's actual definitions.

For instance, the presence of an explicit comparison marker might provide evidence for one type of construction, whereas a predicative identity relation might support another. Whether either feature is decisive must be established from your 12-category codebook.

I would consider extracting these features:

| Feature | Question answered | Why it matters |
|---|---|---|
| Target referent | What person, object or concept is being described? | Separates the animal or plant source from the actual target. |
| Grammatical relation | Is the expression a predicate, modifier, apposition, compound or another construction? | Provides structural evidence rather than relying on vocabulary. |
| Explicit comparison | Is a comparison explicitly expressed? | Helps distinguish explicitly comparative constructions. |
| Identity or predication | Is the source being predicated of the target, literally or figuratively? | Helps investigate nominal-metaphor boundaries. |
| Lexicalisation | Is the expression a conventional idiom or fixed phrase? | Helps distinguish productive figurative constructions from frozen expressions. |
| Context dependence | Is the target or figurative interpretation unclear without surrounding sentences? | Identifies cases needing more context. |
| Evidence span | Which exact words justify the classification? | Makes predictions easier to audit. |

The full set of features should be chosen by reviewing the actual 12 category definitions, rather than adding linguistic attributes simply because they are easy to extract.

### Why might this improve accuracy?

Suppose Qwen3 correctly identifies a figurative expression and its target 90% of the time but struggles with the distinction between two rhetorical constructions.

Asking it to explain everything in free-form prose does not guarantee that the final category will respect the grammatical evidence it identified.

Explicit feature extraction makes those decisions inspectable. It also allows you to identify which stage fails.

For example:

- If the target referent is wrong, investigate context and coreference.
- If the grammatical relationship is wrong, investigate syntactic analysis.
- If the features are correct but the category is wrong, investigate the taxonomy and classification rule.

You would then have a much clearer picture of where the errors originate.

### An even better version: Predict the features separately

Rather than asking a single LLM call to generate every feature and the final label, you could annotate the gold examples with a small number of intermediate linguistic attributes.

Then test whether a simpler classifier can predict those attributes before mapping them to the final category.

This creates a more transparent pipeline:

**Text + context → linguistic features → rhetorical category.**

Some attributes can be detected with rules or dependency parsing. Others may require a learned classifier.

This is particularly attractive for your project because your categories are based on linguistic structure, not merely semantic similarity.

**My recommendation:** Start by testing this approach specifically on nominal metaphors and their most common confusions. Do not rebuild the entire pipeline until you have evidence that the intermediate features help.

---

## 3. Use more literary context: Compare sentence-level and context-enriched classification

Your input is a literary sentence drawn from a novel. That sentence may contain a figurative expression whose interpretation depends on preceding or following sentences.

For example, consider:

> C'était un renard.

Without context, the expression could be interpreted in different ways depending on whether the passage describes a literal animal, a person characterised by cunning, or a name or established expression whose function depends on the narrative.

Task 1 has already decided that the relevant occurrences are figurative, so the challenge for Task 2 is not simply to rediscover figurativeness. It is to understand the rhetorical structure of an expression whose interpretation may be context-dependent.

### Experiment A: Three context windows

Run your existing Qwen3 setup under three conditions.

| Condition | Input | What it tests |
|---|---|---|
| A | Original sentence only | Existing baseline |
| B | Previous sentence + target sentence + following sentence | Whether immediate context improves interpretation |
| C | Target paragraph, or a larger bounded passage where needed | Whether broader narrative context helps |

Keep the prompt, model, generation settings, rules and test examples identical between conditions.

**Mark the target animal or plant expression explicitly.** For example:

```text
CONTEXT:
[Previous sentence]

TARGET SENTENCE:
Cet homme est un véritable loup.

[Following sentence]

TARGET EXPRESSION:
loup

Classify the rhetorical structure of the marked expression.
Do not classify other figurative expressions in the context.
```

The actual target expression and surrounding text would come from your corpus.

This helps the model use context without confusing the target occurrence with another figurative expression elsewhere in the passage.

### Experiment B: Generated contextual enrichment

A related, less conventional technique is to generate auxiliary context about an expression before classifying it.

For example, an auxiliary step might identify what the passage tells us about the person being described and how the animal expression relates to that person. The resulting information is then supplied to the classifier.

Research on context enrichment has reported improvements in metaphor detection on English benchmark datasets, but that does not establish that it will help this French, 12-category task. [MDPI](https://www.mdpi.com/2504-2289/9/9/218?utm_source=chatgpt.com)

I would test generated enrichment only after the real-context experiment.

Why? Because **the original novel is your strongest source of contextual evidence**. Generated text might introduce interpretations that the author never intended or information that is absent from the passage.

### How I would evaluate it

Compare the following:

1. Your existing sentence-level baseline.
2. Real context only.
3. Generated contextual explanation only.
4. Real context plus generated contextual explanation.

Evaluate all four on the same examples.

Record not just total accuracy but nominal-metaphor recall, precision and the specific categories into which its errors move.

It is entirely possible that additional context improves some rhetorical distinctions but does nothing for others.

That is useful information in itself.

---

## 4. Try retrieval-based few-shot prompting, but retrieve examples by linguistic structure

This is one of the most promising experiments that you have not yet tried.

I want to distinguish it from your failed verifier approach.

A verifier asks a second model to reconsider an existing prediction. Retrieval-based few-shot prompting instead provides examples of how the annotation scheme should be applied before the original classification decision is made.

They solve different problems.

Research comparing prompting, retrieval-augmented approaches and fine-tuning for metaphor identification provides a relevant starting point. A 2025 preprint by Fuoli and colleagues compares these approaches and reports systematic disagreements between human and model annotations, including disagreements associated with grey areas in metaphor theory. Its results are encouraging for investigating alternative methods, although its findings do not establish which approach will work best for Écopoétique. [arXiv](https://arxiv.org/abs/2509.24866?utm_source=chatgpt.com)

### The approach

Build a small, curated collection of examples from your existing hand-annotated data.

For each example, store:

- The original French sentence.
- The marked animal or plant expression.
- The correct rhetorical category.
- A short explanation of the relevant linguistic distinction.
- The syntactic construction, where known.
- A similar expression that belongs to a different category, where available.

When a new example arrives, retrieve a few examples that help explain its classification.

The crucial point is that **retrieval should prioritise structural similarity, not just semantic similarity**.

For example, suppose the target expression is a nominal metaphor. Finding another sentence about a fox might be less useful than finding an example involving a different animal but the same kind of predicative construction.

Your model needs to learn the distinction between rhetorical structures, not simply associate particular animal names with particular categories.

### Use contrastive examples

I would favour examples that explicitly illustrate the boundary between two plausible categories.

A prompt might contain:

```text
EXAMPLE 1
Expression: [French example A]
Correct category: [Category A]
Reason: [Relevant grammatical distinction]

EXAMPLE 2
Expression: [French example B]
Correct category: [Category B]
Reason: [Relevant grammatical distinction]

NEW EXPRESSION
[Target passage]

Determine which construction the new expression instantiates.
Use the examples to understand the category boundary, but
classify the new expression from its own linguistic evidence.
```

The examples should be authentic, researcher-annotated passages wherever possible.

### How many examples?

Start with a small number, such as four to eight examples for each query, prioritising the most relevant categories and their competing alternatives.

Compare three conditions:

| Condition | Prompt content |
|---|---|
| A | Your current prompt, without examples |
| B | A small, fixed set of curated examples |
| C | Examples retrieved for the particular expression |

Keep the remaining prompt identical.

Do not immediately put all 12 categories and dozens of examples into the context. That makes it harder to determine whether the gain comes from useful examples or merely from changing the amount and composition of the prompt.

**An important safeguard:** Retrieved examples must come only from the training or development pool. Do not retrieve examples from a held-out test set, and do not use its gold labels to select examples or refine the prompt.

Retrieval is not inherently an overfitting technique. It becomes an evaluation problem when information from the test data influences the system being evaluated.

One further refinement would be to retrieve examples using both sentence embeddings and observable syntactic features. Semantic embeddings alone may retrieve sentences about similar subjects without retrieving the rhetorical construction that matters most.

---

## 5. Benchmark CamemBERT and conventional classifiers against Qwen3

Your idea of training a French-specific classifier is worth pursuing. I would expand it into a small, controlled benchmark rather than going directly to a full fine-tuning project.

Your task has an important characteristic: the label space is fixed at 12 researcher-defined categories, and you already have labelled examples.

That makes supervised classification a natural alternative to repeatedly asking a generative model to interpret an entire taxonomy.

CamemBERT is a French-language model based on RoBERTa and is explicitly designed for downstream tasks including text classification. The Hugging Face documentation provides its model and implementation details. [Hugging Face](https://huggingface.co/docs/transformers/model_doc/camembert?utm_source=chatgpt.com)

### Experiment 1: TF-IDF with a linear classifier

Start with a relatively simple baseline:

**Word and character TF-IDF features + a linear SVM.**

Why bother with something this simple when you have a 30-billion-parameter LLM?

Because your categories have grammatical signatures.

A model using word and character patterns may learn useful distinctions involving:

- Comparison markers.
- Recurrent syntactic constructions.
- Fixed expressions.
- Characteristic lexical patterns associated with compounds.
- Frequent morphological and grammatical forms.

A conventional classifier cannot solve every context-dependent semantic distinction, but it can establish how much of the problem is already recoverable from recurring surface patterns.

You can also test logistic regression, which provides a simple route to inspecting class probabilities.

Treat these models as baselines, not as presumed winners.

### Experiment 2: CamemBERT with a classification head

Train CamemBERT to predict one of the 12 categories directly.

The model receives the text, and the classification head predicts:

\[
\hat{y}=\arg\max_{c\in\{1,\ldots,12\}}P(c\mid x)
\]

Unlike generative prompting, this model is trained directly to distinguish the available labels.

With only 184 annotated examples, full fine-tuning may overfit. That is why I would test more than one approach.

### Experiment 3: Frozen embeddings + a classifier

Use a pretrained French encoder to represent each example as a vector, but initially keep the encoder frozen.

Then train a relatively simple classifier on those representations.

This is a useful intermediate experiment because it reduces the number of parameters being fitted to the small gold dataset.

It also helps answer a practical question: do the representations already contain useful information about the rhetorical structures, or does the model need task-specific fine-tuning to learn the distinctions?

### Experiment 4: Fine-tune the encoder

If the frozen-embedding approach looks promising, compare it against full CamemBERT fine-tuning.

I would include FlauBERT as an additional French-language encoder if compute and implementation time permit.

Here is the benchmark I would actually run:

| Model | Main purpose | Priority |
|---|---|---|
| TF-IDF + linear SVM | Establish a cheap, interpretable baseline | Very high |
| TF-IDF + logistic regression | Compare another conventional classifier | High |
| Frozen CamemBERT embeddings + classifier | Test pretrained representations without full fine-tuning | Very high |
| Fine-tuned CamemBERT | Learn task-specific rhetorical distinctions | Very high |
| Fine-tuned FlauBERT | Compare another French-specific model | Medium |
| Current Qwen3 hybrid pipeline | Existing reference system | Essential |

Keep the rule-based layer as a separate, measurable component rather than assuming that a supervised classifier must replace the entire pipeline.

### What about the 184-example limitation?

Do not fine-tune on all 184 examples and then report accuracy on those same examples. That would measure memorisation and training fit, not generalisation.

Instead, use grouped cross-validation wherever feasible, with examples from the same novel kept together. Literary sentences from the same novel can share vocabulary, style and rhetorical patterns, making a random sentence-level split overly optimistic.

If the classes are too sparse to support that split, you will need additional annotations or a more carefully designed repeated evaluation.

The literature gives you a reason to test fine-tuning, not a guarantee that it will improve your result. For example, the 2025 metaphor-identification study discussed above found fine-tuning promising, but its experiments do not establish that a classifier trained on 184 French literary examples will outperform your Qwen3 pipeline. [arXiv](https://arxiv.org/abs/2509.24866?utm_source=chatgpt.com)

**My prediction:** The most informative first comparison will be your existing pipeline versus TF-IDF/SVM and frozen CamemBERT embeddings. These experiments are relatively easy to interpret and will tell you whether a supervised approach deserves further investment.

---

## 6. Try coarse-to-fine classification instead of making one 12-way decision

Your current system must choose one of 12 categories in a single final classification step.

This is difficult when some distinctions are structurally obvious and others require more nuanced interpretation.

An alternative is to organise the categories into meaningful groups and classify them progressively.

Hierarchical text classification is an established research area in which models use relationships between coarse and fine-grained labels rather than treating every category as independent. Research on hierarchical classification also highlights the importance of designing the hierarchy to match the actual annotation scheme. [MDPI](https://www.mdpi.com/2079-9292/13/7/1199?utm_source=chatgpt.com)

### How this could work for Écopoétique

I would first ask your supervising researcher whether the 12 categories can be grouped by their defining linguistic properties.

For example, a first stage might distinguish broad types of construction, while a second stage determines the particular rhetorical category within that group.

The exact grouping should come from your existing taxonomy. I would not impose a hierarchy without reviewing the 12 definitions.

The conceptual structure would be:

```text
Figurative occurrence
        |
        v
Identify the broad construction type
        |
        +---- Construction group A
        |          |
        |          v
        |    Distinguish its categories
        |
        +---- Construction group B
        |          |
        |          v
        |    Distinguish its categories
        |
        +---- Construction group C
                   |
                   v
             Distinguish its categories
```

### Why might this help?

The initial decision can eliminate categories that are structurally incompatible with the expression.

The second decision then considers a smaller number of candidates.

For example, if your taxonomy distinguishes categories defined by explicit comparative constructions from categories defined by predicative identity, the model could first identify the construction and then apply the appropriate category definitions.

However, coarse-to-fine classification can also propagate errors: if the first stage chooses the wrong group, the correct final category may become unreachable.

Therefore, compare it against your existing flat classifier and inspect both stages separately.

I would not implement this until the actual category definitions have been mapped into a defensible hierarchy.

### A related option: Pairwise classification

If a meaningful hierarchy cannot be constructed, train a small set of discriminators for the most difficult category boundaries.

For example, rather than training a separate classifier for all 66 possible pairs of 12 labels, start with nominal metaphor versus the two or three categories with which it most frequently competes.

Test whether those specialised classifiers can resolve distinctions the general model repeatedly misses.

Because your nominal-metaphor errors are scattered across several categories, you may eventually need more than one discriminator. This approach is therefore best used after analysing the confusion matrix, not before.

---

## 7. Investigate nominal metaphors as a possible annotation problem, not just an NLP problem

This is particularly important for your project.

You have already established that the nominal-metaphor category has a substantial error rate despite several rounds of targeted prompt refinement.

You have also established that the mistakes are not confined to one alternative category.

I would investigate the definition and annotation of this category before investing heavily in additional prompting.

### Build a dedicated nominal-metaphor error set

Collect four groups:

| Group | Examples |
|---|---|
| True positives | Gold label and model prediction are both nominal metaphor |
| False positives | Model predicts nominal metaphor, but the gold label is different |
| False negatives | Gold label is nominal metaphor, but the model predicts something else |
| Boundary cases | Examples for which a knowledgeable annotator could reasonably consider competing categories |

For every example, record the grammatical construction, the intended referent, the gold label, the predicted label and the researcher's explanation.

Then ask your supervising researcher to review the errors without first being influenced by the model's proposed explanation.

### Questions to answer

**Does the category have a sufficiently precise definition?**

An informal description such as "X is Y" may be useful as an initial illustration, but the actual category definition needs to specify which constructions qualify and which do not.

**Are the categories mutually exclusive?**

If the taxonomy permits an expression to be both a nominal metaphor and another kind of rhetorical construction, forcing a single label may be inconsistent with the theory.

**Are there implicit constructions?**

French literary prose contains ellipsis, unusual word order and constructions whose interpretation depends on surrounding text. A pattern that looks nominal in isolation may behave differently in the passage.

**Is the annotation decision based on grammatical form or rhetorical function?**

If one category is defined primarily by syntactic structure and another by rhetorical function, they may overlap unless the codebook explains how to resolve such cases.

### Measure annotation agreement

Ask a second annotator familiar with the taxonomy to independently classify a sample of the disputed examples.

Then examine both the raw agreement and an appropriate agreement statistic, such as Cohen's kappa for two annotators assigning mutually exclusive categories.

The aim is not merely to produce another score. It is to establish whether the gold labels represent a consistent interpretation of the researcher's theory.

If two qualified annotators consistently disagree about the category boundaries, improving the model may require clarifying the annotation scheme first.

Research on metaphor identification supports taking this possibility seriously: Fuoli and colleagues report that many human–LLM discrepancies in their experiments are systematic and reflect grey areas in metaphor theory, rather than simply isolated prediction errors. [arXiv](https://arxiv.org/abs/2509.24866?utm_source=chatgpt.com)

**For me, this is one of the most important investigations in your project.** If the nominal-metaphor category cannot be reliably distinguished by a human applying the current guidelines, no amount of prompt engineering can completely resolve that underlying inconsistency.

---

## 8. Use active learning to select the next examples for annotation

You have a gold set of 184 examples and a corpus containing tens of thousands of figurative occurrences.

That is an excellent situation in which to investigate active learning.

Instead of asking the researcher to annotate another random batch of sentences, use the existing model to identify examples that are likely to be informative.

Active learning is designed to reduce annotation effort by selecting examples that may be particularly valuable for a classifier. However, research also cautions that active-learning strategies do not reliably outperform simpler alternatives in every setup, so the selection procedure itself needs evaluation. [ACL Anthology](https://aclanthology.org/2024.emnlp-main.1240/?utm_source=chatgpt.com)

### Three ways to select examples

**A. Model uncertainty**

Select examples for which the classifier has difficulty choosing among categories.

For a discriminative classifier, prediction probabilities can provide uncertainty measures. For Qwen3, do not assume that its verbal confidence is calibrated; use repeated-prompt disagreement or alternative-model disagreement only as selection signals to investigate.

**B. Pipeline disagreement**

Select examples for which different components reach different conclusions.

For instance, the syntactic fallback might identify a construction that the LLM classifies differently. Those examples may reveal weaknesses in the rules, parser or classification criteria.

**C. Diversity**

Select structurally diverse examples rather than repeatedly annotating very similar passages.

This matters because an uncertainty-based strategy can otherwise concentrate on many near-duplicate expressions, giving less value than a diverse batch.

### What I would do

Start by selecting a batch containing:

- Nominal-metaphor candidates that the current system classifies inconsistently.
- Examples where the syntactic fallback and LLM disagree.
- A diverse sample of difficult examples from other categories.
- Some randomly selected examples to provide a comparison.

Have the researcher annotate the batch, add the adjudicated examples to the training pool, and retrain or update the system.

Evaluate each iteration on data that have not been used to choose or annotate the new training examples.

Compare the resulting improvement against adding the same number of randomly sampled annotations.

This will tell you whether targeted annotation is actually more efficient for this task.

### How many additional examples?

I would begin with a modest pilot batch, perhaps 50–100 additional annotations, rather than assuming that you need thousands of examples before starting.

The number is only a starting point. What matters is that the batch adds useful information about difficult boundaries and underrepresented categories.

If the supervised baselines are promising but unstable, a larger set of carefully annotated examples may provide more value than another extensive series of prompt variations.

---

## 9. Improve the decision policy of your existing hybrid pipeline

Not every occurrence needs to be sent through the same sequence of increasingly complex models.

You already have:

1. Rule-based classification.
2. A spaCy syntactic fallback.
3. Qwen3 for ambiguous cases.

I would preserve this structure but evaluate whether each stage is being used appropriately.

### A. Measure each layer independently

Record the prediction and whether it was correct at every stage.

For example:

| Component | Key measurement |
|---|---|
| Rule-based layer | Precision and recall on cases it handles |
| spaCy fallback | Precision and recall on cases not handled by the rules |
| Qwen3 | Accuracy and per-category performance on cases that reach it |
| Complete pipeline | Overall accuracy and macro-F1 across the evaluation set |

This will expose whether the problem is primarily in the rules, parsing or LLM fallback.

An overall score alone cannot answer that question.

### B. Review rules that produce false positives

Your rule-based layer is valuable because it prevents the LLM from misclassifying clear, conventional cases.

However, every hard-coded rule should have an explicit evaluation.

I would keep rules for constructions that have been shown to be reliably identifiable, while treating ambiguous patterns as evidence rather than automatic classification decisions.

For example, a grammatical pattern might narrow the candidate categories without uniquely determining the rhetorical function.

In that situation, use the pattern to guide the downstream classifier rather than force a potentially incorrect label.

### C. Introduce an abstention option

One potentially useful improvement is to let the system defer genuinely ambiguous cases for manual review.

The pipeline would then have three possible outcomes:

- Automatic classification.
- Classification with a lower level of certainty.
- Abstention and human review.

This does not magically increase accuracy across all examples. Instead, it allows you to measure the trade-off between automated coverage and reliability.

For example, you might compare overall accuracy when the system classifies 100% of cases against accuracy when it automatically classifies only the 80% of cases it can handle most reliably.

The precise threshold should be selected using development data.

For a digital humanities project, this can be useful because the priority may be reliable corpus-level analysis rather than insisting that every individual occurrence receive an automatic label.

---

## 10. A few additional experiments I would consider

Beyond the main approaches, I would consider these targeted experiments.

### Contrastive prompt instructions

Your prompt already includes linguistic reasoning steps. Rather than adding more general instructions, provide explicit examples of the differences between competing categories.

For each difficult boundary, show an example of each category and explain the decisive linguistic evidence.

This is different from simply making the definitions longer. The goal is to teach the model what distinguishes one category from another.

I would concentrate on the boundaries revealed by your error analysis.

### Synthetic examples, with human validation

You could generate examples illustrating difficult constructions and use them to augment training data for a smaller classifier.

For instance, a generator could produce examples designed to distinguish a particular rhetorical construction from its nearest alternative.

But synthetic labels can be wrong, particularly when the categories themselves are subtle. I would have the researcher validate examples before adding them to the training set.

I would not use synthetic examples as a replacement for genuine corpus annotations or as evidence of improved test accuracy.

### Teacher–student training

Once you have a well-evaluated teacher system, you could use its predictions to generate provisional labels for additional corpus examples and train a smaller classifier on them.

The existing gold examples should remain the trusted reference. Before using automatically labelled data, audit the predicted labels and prioritise reliable cases.

This could eventually make the pipeline cheaper and faster across the complete corpus, but I would not start here: the teacher's errors could simply be transferred to the student.

### Compare the influence of target highlighting

Run a controlled experiment in which the target animal or plant expression is explicitly marked, compared with the original sentence as supplied to the model.

You may find that highlighting helps prevent the model from classifying another figurative expression or focusing on the overall meaning rather than the particular construction.

This is an inexpensive experiment and is easy to evaluate without changing the underlying architecture.

---

# 11. My recommended experimental plan

Given the time already invested in your existing system, I would prioritise the experiments as follows.

| Priority | Experiment | Main question | Expected value |
|---|---|---|---|
| 1 | Audit nominal-metaphor errors and annotation consistency | Are the category boundaries sufficiently precise? | Very high |
| 2 | Add a frozen, independent evaluation protocol | Are apparent gains likely to generalise? | Essential |
| 3 | Compare sentence-only versus real-context prompting | Is the current input missing important evidence? | High |
| 4 | Test structured feature extraction | Can we separate linguistic analysis from category assignment? | Very high |
| 5 | Benchmark TF-IDF/SVM and frozen CamemBERT embeddings | Can a supervised classifier learn useful structural distinctions? | Very high |
| 6 | Test retrieval-based few-shot prompting | Do authentic contrastive examples improve category decisions? | High |
| 7 | Test fine-tuned CamemBERT | Does supervised learning improve on the current Qwen3 system? | High |
| 8 | Annotate an active-learning batch | Can a relatively small amount of targeted annotation improve performance? | Very high |
| 9 | Test coarse-to-fine classification | Can a meaningful category hierarchy simplify the decisions? | Medium to high |
| 10 | Add abstention and confidence-based routing | Can the system improve the reliability of its automatic predictions? | High for production |

These priorities are not predictions that every experiment will improve accuracy. They reflect how much useful information each experiment can provide, given the current bottlenecks.

## How to evaluate the experiments properly

Use one consistent evaluation procedure for all the candidates.

**First, separate development from evaluation.** Freeze the existing 184-item set if it has already been used for repeated prompt refinement, or use grouped cross-validation for development and obtain an additional independently annotated test set.

**Second, split by novel wherever possible.** Avoid having sentences from the same novel in both training and test partitions. If a class is represented in too few novels to support this, document the limitation rather than quietly falling back to a potentially optimistic random split.

**Third, report multiple metrics.** Use accuracy, macro-F1 and per-category precision and recall. Inspect the confusion matrix, particularly for nominal metaphors.

**Fourth, keep the comparison controlled.** When comparing context windows, prompt variants or models, keep the evaluation examples identical. Record the exact prompt, model version, rules and inference settings for each run.

**Finally, quantify uncertainty.** Report confidence intervals where appropriate, and use paired comparisons of predictions on the same held-out examples. Small differences in accuracy should not be treated as definitive evidence of improvement.

---

# 12. If I were implementing just three improvements first

I would start with these three.

**First, investigate the nominal-metaphor category.** Build an error set, inspect the other categories receiving its false negatives, and get the supervising researcher to adjudicate disputed examples. This addresses the possibility that the model is struggling with an unclear or overlapping taxonomy.

**Second, test a combination of real context and explicit linguistic features.** Compare sentence-only and context-enriched inputs, while separating target identification, grammatical structure and final rhetorical classification. This is the most direct way to determine whether the current prompt's reasoning process is failing because of missing evidence or because the final category boundaries are difficult to learn.

**Third, benchmark a frozen CamemBERT representation with a simple classifier, alongside TF-IDF/SVM.** These provide useful supervised baselines without immediately committing to an extensive fine-tuning project. If they perform well, proceed to fine-tuning CamemBERT and consider adding targeted annotations.

I would then test retrieval-based few-shot prompting against your best existing prompt, using researcher-annotated contrastive examples from the training data.

One final point: **I would not set an arbitrary target such as 80% accuracy before seeing these results.** A meaningful improvement depends on the category distribution, annotation consistency and how well the system performs on unseen novels. Your current 71.2% is a useful baseline, but the most valuable next step is to establish which part of the problem is responsible for the remaining errors.

That diagnosis will determine whether the most productive investment is better linguistic rules, improved context, a supervised classifier, additional annotations or a clearer rhetorical taxonomy.






































another answer: 
You have built a remarkably rigorous, honest, and sophisticated pipeline. Achieving **71.2% accuracy** across **12 fine-grained, highly nuanced French rhetorical categories** using an LLM zero-shot/CoT setup is an impressive achievement—especially given how slippery figurative language and French stylistics can be.

Your diagnosis of the remaining bottlenecks (particularly the 50% error rate and scattered confusion on **nominal metaphors**—*“X is Y”* structures) points to a fundamental challenge: LLMs struggle to draw crisp boundaries between abstract linguistic categories when presented with a flat 12-way choice.

Here are several advanced, untried strategies designed to break past the 71.2% ceiling, addressing both the nominal metaphor problem and the limitations of your current setup.

---

### 1. Re-architecting the LLM Call: Hierarchical (Decision-Tree) Classification

Right now, you are asking Qwen3-30B to pick 1 out of 12 categories in a single shot. This creates massive cognitive load and increases the chance of scattered confusion.

Instead, split the classification into a **hierarchical decision tree** that mirrors how a human stylist or linguist analyzes a sentence:

* **Step 1 (Binary/Ternary Split):** Is the figurative structure explicit (like a simile with *comme*), relational/modifying (like a compound noun or adjective), or an identity claim (*être* / direct equation)?
* **Step 2 (Fine-Grained Category):** Once the model knows *which branch* of the rhetorical tree it's on, narrow the choices down to 3–4 specific categories instead of all 12.

**Why this helps the nominal metaphor problem:** Nominal metaphors ("his heart is a wolf") get confused with other categories because the model gets distracted by the broader semantic context. Forcing the model to first decide *“Is this an identity statement (*X = Y*) or a comparison (*X ~ Y*)?”* drastically cuts down error variance before it even tries to name the exact sub-category.

---

### 2. Unlocking the Small-Model Fine-Tuning Route via "Silver Data" (Pseudo-Labeling)

You correctly identified that fine-tuning a French-specific BERT model (like **CamemBERT** or **FlauBERT**) is theoretically the strongest path forward, but was blocked by a small gold set (184 rows) that makes a proper train/test split impossible.

You can bypass this limitation using **self-training / pseudo-labeling** with your existing pipeline:

1. **Leverage the unlabeled corpus:** You have tens of thousands of sentences processed by your rule-based and spaCy layers, plus high-confidence predictions from Qwen3-30B.
2. **Mine high-confidence outputs:** Run your current pipeline over a few thousand unlabelled sentences. Filter strictly for outputs where the CMT chain-of-thought shows extreme logical consistency, or where rules/syntax caught unambiguous patterns.
3. **Build a "Silver" Dataset:** Combine your 184 gold rows with, say, 1,000–2,000 high-confidence silver rows.
4. **Fine-tune CamemBERT:** Split *that* combined dataset into train/validation/test.

Because discriminative models like CamemBERT are exceptionally good at picking up subtle syntactic markers and token-level distributions (which govern things like nominal metaphors), a fine-tuned encoder model often obliterates generative LLMs on classification tasks once it has a few hundred examples per class.

---

### 3. Contrastive Prompting & Negative Constraints for "Nominal Metaphors"

Since nominal metaphors are your main bleeding edge, your current prompt likely defines *what* they are, but doesn't explicitly tell the model *what they are frequently confused with*.

Add a **negative constraint block** specifically targeting the boundary between nominal metaphors and neighboring categories in your CMT prompt:

> **CRITICAL DISTINCTION FOR NOMINAL METAPHORS:**
> Do not confuse a Nominal Metaphor (*"He is a wolf"*) with:
> * A Simile (*"He is like a wolf"* / *"cunning as a wolf"*): requires an explicit comparison marker or shared quality adjective.
> * A Frozen Idiom: if the phrase has lost its literal compositional meaning entirely (e.g., fixed expressions), classify it as an idiom, not a novel nominal metaphor.
> * A Metonymy/Qualifying Compound: if the animal word is modifying another noun rather than forming a direct copula identity claim, it belongs to [Category X].
> 
> 

---

### 4. Curated Static Few-Shot Anchors (Carefully Selected Prototypes)

You noted that retrieval-based few-shot examples risk overfitting, and a verifier LLM just amplifies confident mistakes. However, **static, hand-curated prototypes**—injecting exactly *one* golden exemplar per category directly into the system prompt—can anchor the model's spatial understanding of the categories without dynamic retrieval noise.

For the nominal metaphor category in particular, pick the cleanest, most unambiguous example from your corpus and hardcode it into the prompt as the canonical archetype of "Nominal Metaphor."

---

### Summary Recommendation

If you want the highest ROI with the lowest engineering overhead next:

1. **Try the Hierarchical Prompting approach first.** Restructure the LLM's task into a two-step questionnaire (Structure Type $\rightarrow$ Sub-category). This directly targets the scattered confusion pattern of the nominal metaphor category.
2. **If that plateaus, pivot to CamemBERT fine-tuning via silver-data pseudo-labeling.** Using Qwen3-30B to bootstrap a training set for a dedicated French encoder model is the most robust way to permanently solve fine-grained stylistic classification.

Which of these directions feels most aligned with your current timeline and compute setup for the internship?



















another answer: 


1. High-Level Diagnosis & Architecture Critique

Your hybrid pipeline is exceptionally well-engineered for a Digital Humanities (DH) task. The fact that you have a clean 71.2% accuracy based on an uninflated, stable prompt evaluated against a rigorous gold-standard set is impressive for a 12-class rhetorical classification problem.
Your diagnosis regarding nominal metaphors ("X is Y") having a ~50% error rate scattered across multiple categories is a classic indicator of a semantic-structural mismatch in LLMs. Generative LLMs struggle with nominal metaphors because they evaluate semantics over strict syntactic structure. To a model like Qwen3, "Ce professeur est un vieux chêne" (Nominal Metaphor) and "Il restait immobile comme un vieux chêne" (Simile) are semantically identical (an old, stubborn, deeply rooted person). The model focuses on the conceptual mapping (Conceptual Metaphor Theory), which causes it to bleed the structural category boundaries into whatever other rhetorical category shares that semantic flavor.
To push past 71.2%, you need to transition from relying on an LLM to balance both grammar and abstract theory simultaneously, and instead force a separation of concerns.

2. Strategy Analysis: Evaluating Your Unexplored Options


Option 1: Fine-tuning a small French Encoder (CamemBERT / FlauBERT)

• The Verdict: Highly Recommended, but with an architectural twist.
• The Reality Check on Data Size: The literature is correct that encoder-based models (like CamemBERT-large) saturate early on downstream classification tasks, but 200 examples is too small for a 12-class split. With 12 categories, 200 examples averages out to just ~16 examples per class. If you try a standard train/test split (e.g., 140 train / 60 test), your model will fail to generalize to the rarer categories and will overfit.
• How to salvage this: Do not use CamemBERT as a raw text classifier from scratch. Instead, use SetFit (Sentence Transformer Fine-Tuning) or contrastive learning. SetFit allows you to fine-tune a CamemBERT-based sentence transformer using few-shot contrastive pairs (turning your 16 examples per class into thousands of positive/negative triplets). This achieves high accuracy with minimal data.

Option 2: Context-Enrichment Prompting

• The Verdict: Strong candidate for an immediate, zero-code-change trial.
• Why it works for metaphors: If you ask a model to classify a sentence immediately, it uses its internal weights to predict the token sequence of the category name. If you force it to first write a linguistic "exegesis" or a structural blueprint of the sentence, it populates its context window with the explicit syntactic rules it needs to make the final decision.

3. Concrete Action Plan & Immediate Adjustments


Step 1: Fix Nominal Metaphors via Syntactic Feature Injection (Low Code)

Since your pipeline already has a spaCy dependency parsing layer (Layer 2), use it to explicitly flag nominal metaphor structures before the text reaches the LLM.
• The Fix: Write a spaCy script using the Matcher or DependencyMatcher to detect the classic French copular and appositive structures:
	• Copula: [Noun] + [être / sembler / paraître] + [Animal/Plant Noun] ("Cet homme est un lion")
	• Apposition: [Noun] + , + [Animal/Plant Noun] + , ("Cet homme, un vrai lion, a foncé...")
• The Implementation: If spaCy detects this exact syntactic skeleton, append a structural tag to the string passed to the LLM, or inject it as a metadata variable: [SYNTAX_NOTE: This sentence structurally equates Subject X directly to Object Y via a copular verb or apposition without using comparison words like 'comme']. This breaks the model's semantic blindness.

Step 2: Implement Context-Enrichment (Prompt Update)

Modify your Tier 3 Qwen3 prompt to enforce "Structural Isolation" before classification. Do not let the model output the category until it has mapped the grammar.
Update your prompt sequence to require this exact output structure:
markdown
1. TARGET WORD: [Extract the animal/plant word]
2. SYNTACTIC RELATION: [Identify the exact grammatical link between the target word and its subject. Is there a copular verb (être)? Is there a comparative tool (comme, tel quel)? Is it a noun modifier (d'éléphant)?]
3. LITERAL TRANSFORMATION: [Write out a dummy sentence stripping the metaphor but keeping the exact syntax, e.g., "X est un Y"]
4. RHETORICAL CATEGORY: [Final Selection]
Use code with caution.

Step 3: Expand the Gold Standard to a "Silver Standard" for Fine-Tuning

If you want to move to a fine-tuned CamemBERT/SetFit architecture, you need more data. Use your existing Tier 3 pipeline (which is already 71.2% accurate) to auto-label 2,000 sentences from your remaining pool of tens of thousands.
• Filter out any sentences where the LLM's classification entropy is high (i.e., keep only the ones where it is highly confident or where Layer 1/2 handled it).
• Use this 2,000-sentence "Silver Standard" dataset to fine-tune CamemBERT, and then evaluate that fine-tuned model against your pristine, hand-annotated 184-item Gold Standard set. This avoids data-leakage and solves your data scarcity problem.

4. Copy-and-Paste Project Summary for Communities

Below is a clean, self-contained markdown summary of your project, architecture, and current blockers. You can paste this directly into Reddit (e.g., r/LanguageTechnology, r/LocalLLaMA), Discord, or academic forums to solicit advice.
markdown
### Project Overview: NLP Classification of Fine-Grained Rhetorical Structures in French Literature

**Project Name:** Écopoétique (Sorbonne Université / UPPA)
**Objective:** Analyzing how the non-human world (animals/plants) is represented in a corpus of 925 contemporary French novels. We are specifically investigating whether literature treats the non-human world as passive scenery or as an entity with agency.
**The Current Task:** We have isolated tens of thousands of sentences containing *figurative* uses of animal/plant words. We need to classify these sentences into **12 fine-grained, linguistically defined rhetorical categories** based on French stylistics theory (e.g., similes (*comme un loup*), nominal metaphors (*cet homme est un loup*), qualifying compounds (*une mémoire d'éléphant*), frozen idioms (*avoir des papillons dans le ventre*), etc.).

### Technical Problem & Current Architecture
This is a complex multi-class NLP problem because classes are defined by subtle grammatical/syntactic structures and rhetorical patterns rather than topic vocabulary. 

Our current production pipeline is a **3-tier hybrid setup**:
1. **Rule-Based Layer:** Regex and lexicon matching for fixed idioms, endearment terms, and rigid naming-verb constructions.
2. **Syntactic Fallback:** spaCy dependency parsing for clear grammatical signatures missed by rules.
3. **Generative LLM Layer:** Remaining sentences are sent to a locally hosted **Qwen3-30B (via Ollama)** using structured Chain-of-Thought (CoT) prompting grounded in Conceptual Metaphor Theory (CMT).

### Current Baseline & What We Have Tried
We are sitting at a highly stable, honest **71.2% accuracy** (131/184 correct) on a hand-annotated gold-standard test set. 

Here is what we have exhaustively tested and ruled out based on performance tracking:
*   **Alternative Models:** Swapping Qwen3-30B for DeepSeek-R1 (32B), Gemma 3, Mistral NeMo (12B), or Mistral Small (24B) consistently underperformed our current baseline (the 12B architectures dropped performance by ~30 percentage points).
*   **LLM Multi-Pass Verifiers:** Adding a second LLM call to act as a critic/verifier systematically damaged accuracy (in one category, dropping it from 92% to 31%) because the model confidently doubles down on incorrect structural assessments.
*   **Majority Voting / Self-Consistency:** Failed to yield gains because the LLM's errors are systematic and confident, not stochastic noise.
*   **Prompt Engineering:** Hyper-targeted linguistic prompt adjustments yielded a cumulative ~3.2% increase to get us to our current 71.2%, but we have hit diminishing returns.

### Current Bottlenecks & Open Questions
1. **The Nominal Metaphor Problem:** The "X is Y" structural pattern has a ~50% error rate. Its misclassifications are bleeding randomly into multiple other categories, suggesting the LLM is prioritizing semantic similarity over strict grammatical structure.
2. **Fine-Tuning vs. Prompting:** We want to explore fine-tuning a smaller, dedicated French encoder model (like `CamemBERT` or `FlauBERT`). However, our gold-standard annotated data consists of only ~184 items. 
    *   *Question:* Is there an elegant way to leverage few-shot contrastive frameworks (like SetFit) on a 12-class problem with this little data? Or should we use our current 71.2% pipeline to bootstrap a larger "silver-standard" training set?
3. **Context Enrichment:** Has anyone seen significant success using context-enrichment prompting (forcing the LLM to generate a linguistic/structural blueprint of a sentence's syntax *before* declaring its class tag) for metaphor classification tasks?
Use code with caution.
To help narrow down the implementation of these steps, let me know:
• What does your current distribution of classes look like within those 184 gold-standard sentences? (Are nominal metaphors well-represented, or are they a minority class?)
• Would you prefer to look at the spaCy dependency pattern code needed to catch nominal metaphors, or the SetFit/CamemBERT implementation setup first?

















another answer:

Your history already rules out the usual quick fixes. Here is what I'd do, in priority order.

**1. Fix the evaluation first (highest leverage)**
- Prompt refinements derived from reading misclassified gold items, then re-scored on those same items, mean your 71.2% is optimistic. It's a dev-set number, not a test-set number. With n=184 the 95% CI is also about ±6.5 points, so most 0-1 point gains are noise.
- Split the gold set into dev and test, or annotate 150-250 more items. Draw the new items from the pipeline's low-confidence outputs, which is cheap active learning.
- Have a second annotator label about 60 nominal-metaphor items and compute Cohen's kappa. Scattered errors in one category often mean the boundary is fuzzy for humans too. If kappa is low, the fix is taxonomy work with your supervisor (merge or sharpen categories, add decision rules), not modelling.

**2. Split the 12-way decision into feature questions plus a decision tree**
This is probably the best untried idea for the prompt-based path. Instead of asking the LLM for a category, ask 5-8 narrow questions, each answered yes/no or from a short list:
- Is there an explicit comparison marker (*comme*, *tel*, *plus… que*)?
- Is there an equative or copular verb, or an implicit one?
- Is the vehicle the head or a modifier (*de* complement)?
- Is it a fixed expression?
- Is the target person, object, or abstract?

Then code the mapping from answers to category yourself. Models answer narrow questions far more consistently than they apply a 12-way taxonomy, and the theory lives in auditable code. You can also feed the spaCy parse and the bracketed vehicle span into those questions.

**3. Static curated few-shot examples**
Put 2-3 hand-picked examples per category in the prompt, plus contrastive minimal pairs for the nominal-metaphor boundaries. Take them from outside your test split. Retrieval of similar examples is also fine once you have a proper train/test split. Your overfitting worry only applies if examples come from the evaluation rows.

**4. Fine-tuning, evaluated honestly without more data**
- Run repeated stratified 5-fold cross-validation on the 184 items. That gives an honest estimate without a held-out set.
- Try CamemBERT/FlauBERT, and also a LoRA fine-tune of a smaller Qwen3 (8B/14B). For subtle structural categories, LoRA on a generative model often beats a BERT classifier.
- Stack them: use the LLM's step outputs (vehicle, target, feature answers) as extra input to the classifier.
- Augment with LLM-generated examples per category, validated by the researcher, but only ever into the training folds.

**5. Cheap things worth testing**
- Constrained or JSON-schema output in Ollama, with temperature 0.
- Add the previous and next sentence, with the target span marked.
- Compare thinking on vs. off, and the Instruct-2507 vs. Thinking-2507 Qwen3 variants.
- Compare French vs. English instructions with French examples.
- Context-enrichment prompting, as you planned. It costs little.

**6. Use confidence and humans where they matter**
- Extract token logprobs or feature-agreement scores. Look at accuracy at partial coverage: if the top 70% most confident predictions are 85%+ accurate, route the rest to your supervisor for manual review.
- For the research question, per-sentence accuracy matters less than corpus-level proportions. Use the confusion matrix to correct category frequency estimates (adjusted classify-and-count) and bootstrap confidence intervals. Scattered errors in one category wash out much better than systematic confusion, which is a good argument for the paper.

**Suggested order:** annotation split and kappa → feature-question decomposition → static few-shot → cross-validated fine-tune. I'd expect the first three to give the biggest gains, and the first one tells you how high the ceiling actually is.

I can sketch the feature-question schema and decision tree for your 12 categories if you paste the category definitions.



**Multi-agent research summary (relevant to your setup)**

Recent work on multi-agent LLM systems for long documents, classification, and narrative tasks shows a few recurring, practical patterns that fit local models (Qwen3-30B + Mistral-Small), ~80 gold French novels, and 7 narrative dimensions:

### Core architectures that work
- **Leader + member (divide-and-conquer)**: Document split into chunks → member agents process their chunks → leader aggregates via multi-round discussion + inter-member communication to catch hallucinations. LongAgent-style systems let small-context models handle 100k+ token texts and beat single large models on multi-hop reasoning. Directly upgrades your existing map-reduce.
- **Specialized role agents**: Distinct agents for different analytical lenses (e.g., Lexical, Contextual, Logic, Consensus, Explainability; or theory-specific roles for narrator type, journey structure, autobiographical signals). A controller routes low-confidence cases or rare categories to the right specialists. Used successfully for text classification and screenplay/narrative structure analysis.
- **Hierarchical / supervisor teams**: A supervisor routes subtasks to specialist teams (e.g., one team for rare dimensions, another for dense scanning). Common in LangGraph-style systems for document processing.
- **Reviewer / critic / consolidator agent**: One agent produces the classification + evidence; a second agent cross-checks consistency, sustained patterns, and conflicts with retrieved gold examples. Strong results in story annotation and long-document QA.
- **Parallel competition + evaluator**: Multiple agents independently solve the same ambiguous subtask; a central evaluator scores on factuality/coherence and picks the best. Useful for rare categories where single-model confidence is low.
- **Debate vs pure voting**: Multi-agent debate (agents critique each other’s rationales) helps on complex/ambiguous cases, but several studies find that **simple majority voting / soft ensemble of independent runs already captures most of the gain**. Debate is more expensive and can introduce social-proof bias or decoy signals if memory is poorly managed. Prefer debate only for the hardest rare-category cases.

### Narrative / literary-specific findings
- Multi-agent systems that operationalize narratological theory (Field/Snyder beats, Genette-style features, arc types) into specialized agent roles outperform single-LLM baselines on structure detection and give better interpretability (agent disagreement itself flags structural ambiguity).
- Two-agent prompt-refinement loops (one generates annotation prompts / evidence, the other reconstructs or critiques) improve story annotation quality.
- For rare signals, specialization + disagreement detection is more reliable than forcing consensus.

### Practical caveats for your constraints
- Token cost scales roughly linearly with number of agents/rounds. With local 30B-class models this is feasible but not free—keep the full multi-agent path for uncertain or rare-category cases only.
- Pure debate without strong evidence grounding can amplify confident wrong majorities (you already saw this with same-model self-consistency).
- Structured intermediate outputs (JSON schemas for evidence per dimension) make aggregation far more reliable than free-text discussion.
- Small gold set → retrieval of similar labeled novels as shared “memory” or few-shot context for the agents is high-leverage.

Frameworks you can run locally: LangGraph (best control for hierarchical + conditional routing), CrewAI (fast role-based teams), or a lightweight custom loop if you want zero extra dependencies.

---

**What to do next (concrete, ordered plan)**

1. **Immediate high-ROI upgrade (1–2 days of work)**  
   Turn your current best pipeline (especially the promising holistic reduce) into a minimal multi-agent system:
   - **Chunk/Member agents** (Qwen or Mistral): process the 9 chunks or 24 dense slices → emit structured evidence (JSON: dimension scores, key quotes, confidence, “sustained?” flag).
   - **Leader/Aggregator agent**: receives all structured outputs + optional retrieved similar gold novels → decides final labels with explicit sustained-pattern reasoning.
   - **Critic agent** (run only on disagreement or low confidence): challenges the leader’s decision for rare categories using the same evidence + gold exemplars.
   - Keep your dense-scan overrides and counting rules as hard constraints the Leader must respect.

2. **Add the three techniques you already planned, inside the agent system**  
   - Retrieval few-shot: embed gold novels; retrieve top-k similar ones and inject them as shared context for Leader and Critic (dimension-specific retrieval is even better).  
   - Cross-model: let one agent be Qwen-driven and another Mistral-driven (or run parallel independent pipelines and vote).  
   - Confidence escalation: cheap single-agent or classifier first pass → only escalate to full multi-agent (or dense-scan) when confidence is low or a rare category is predicted.

3. **Target the rare categories explicitly**  
   Create 2–3 specialist agents (or specialized prompts) only for the dimensions where you have the biggest pain (non-human narrator, autobiographical, sustained journey). Route only those dimensions through the expensive path. Use agent disagreement as an explicit signal that the case needs human review or extra retrieval.

4. **Evaluation discipline**  
   - Hold out a clean test set from the ~80.  
   - Measure both overall accuracy and rare-category F1.  
   - Log agent disagreements—they are diagnostically valuable for narratology.  
   - Compare against your current best single-pipeline numbers before expanding the agent graph.

5. **Only after the above shows gains**  
   Experiment with light debate (1–2 critique rounds) on the hardest subset, or a hierarchical supervisor that decides which specialist team to call. Avoid full multi-round debate on every novel—cost will explode with limited local hardware.

Start with the Leader + structured Members + Critic-on-uncertainty skeleton. It directly extends the map-reduce and holistic-reduce work that already showed promise, stays fully local, and gives you the specialization and cross-checking that the research shows helps most on long literary texts and rare narrative signals. Once that baseline is measured, the retrieval and cross-model pieces slot in cleanly.

Yes — that is the right next step, and the recommendation is grounded in the research I ran.

I searched recent multi-agent work on long-document understanding, text classification, narrative/literary analysis, and ensemble/debate setups (LongAgent-style leader+members, DocAgent/reviewer patterns, specialized-role classification agents, hierarchical supervisors, debate-vs-voting studies, and narrative-structure multi-agent systems). The patterns that consistently help with long texts + rare/abstract categories are exactly the ones I prioritized for you:

- Structured member agents + leader aggregator (upgrades your existing map-reduce)
- Critic/reviewer only on uncertainty or rare categories (avoids wasteful full debate)
- Retrieval of similar gold examples as shared context
- Cross-model (Qwen + Mistral) as soft ensemble or parallel agents
- Confidence-based escalation so you only spend compute where it matters

These map cleanly onto your constraints (local 30B-class models, ~80 gold French novels, 7 dimensions, rare categories that have already resisted simpler methods).

### Confirmed next action
1. Implement the minimal multi-agent skeleton first:  
   Member agents emit structured evidence from chunks/slices → Leader decides with holistic/sustained reasoning → Critic triggers only on low confidence or rare-label predictions.

2. Immediately fold in the three techniques you already planned (retrieval few-shot of gold novels, Qwen↔Mistral cross-model, confidence escalation).

3. Measure on a held-out portion of your gold set (overall + rare-category F1) before adding more agents or debate rounds.

That sequence is the highest-leverage, lowest-risk path given what you have already tried and what the literature shows works. Once you have numbers from this version, we can decide whether to expand the agent graph or double down on retrieval/specialists.



**Yes — there are better or complementary models, and smart combinations that fit your exact constraints (local, French novels, long context, rare narrative categories, multi-agent setup).**

### Strongest single-model upgrades (Oct 2026 local landscape)
Your current pair (Qwen3:30b + Mistral-Small) is already solid, but these are the ones currently ranking highest for French literary quality, long-document reasoning, and local deployability:

| Priority | Model | Size / Type | Why it helps your task | Approx. VRAM (Q4/Q5) | Notes |
|----------|------|-------------|------------------------|----------------------|-------|
| **1** | **Qwen3.8-27B** (or Qwen3.6-27B) | Dense 27B | Best local French writing + reasoning among open models; strong on sustained structure and rare signals | 16–18 GB | Direct upgrade or replacement for your Qwen3-30B. Reasoning mode gives big gains in French. |
| **2** | **Magistral Small 24B** or **Mistral Small 3.2/4** | 24B dense / newer MoE | Native French strength, excellent literary register, 128–256k context | 14–16 GB | Best pure-French open models right now. Keep or upgrade your Mistral-Small with these. |
| **3** | **Gemma 4 31B** | Dense 31B | Top scores on document analysis / long-text extraction; very good French | 19–22 GB | Excellent for dense-scan and evidence extraction roles. |
| **4** | **DeepSeek-R1-Distill 32B** (or QwQ-32B) | 32B reasoning distill | Superior chain-of-thought for abstract narratological decisions (rare categories, holistic sustained patterns) | 18–20 GB | Use only for the Leader/Critic agents or hard rare-category cases. |
| **5** | **Llama 4 Scout** (17B active MoE) | MoE ~109B total | Massive context (up to 10M tokens claimed) — useful if you ever want whole-novel single-pass | Higher, but efficient | Only if you have ≥24–32 GB and want to experiment with near-full-novel context. |

Avoid pure coding-oriented or very small models; they lose literary nuance.

### Best model combinations for your multi-agent system
Diversity beats “same family twice”. Recommended practical setups:

1. **Core recommended ensemble (lowest risk, highest gain)**  
   - Member / Chunk agents → **Qwen3.8-27B** or **Gemma 4 31B** (strong extraction + structure)  
   - Leader / Aggregator → **Magistral Small 24B** or **Mistral Small 3.2** (best French literary judgment)  
   - Critic / Rare-category specialist → **DeepSeek-R1-Distill 32B** or another Qwen reasoning variant  
   Soft-vote or confidence-weighted between the two French-strong models on final labels.

2. **Maximum French + reasoning**  
   Magistral/Mistral Small + Qwen3.8-27B (reasoning on) + DeepSeek-R1-32B for the hardest dimensions only.

3. **Lightweight / faster iteration**  
   Keep your current Qwen3-30B + Mistral-Small, but add **Gemma 4 31B** as a third voter on rare categories and the holistic reduce step. Three-model majority already gives most of the ensemble benefit without huge cost.

4. **If you have more VRAM (≥40–48 GB)**  
   Run two strong models in parallel (Qwen3.8-27B + Magistral 24B) for every novel and only escalate the Critic when they disagree. This is the cleanest cross-model setup.

### Practical advice for your next step
- Stick with the multi-agent skeleton I outlined earlier (structured Members → Leader → Critic-on-uncertainty).
- Swap in **Qwen3.8-27B** (or keep your 30B if already tuned) + **Magistral Small / latest Mistral Small** as the primary pair.
- Add **DeepSeek-R1-Distill 32B** or **Gemma 4 31B** only for the Critic or rare-dimension specialists — do not run the full heavy model on every chunk.
- Test on a small held-out slice first (especially the dimensions that jumped with the holistic prompt). Measure rare-category F1, not just overall accuracy.
- Quantization: Q4_K_M or Q5 is usually enough for these; Qwen3.8 often keeps quality surprisingly well even at Q4.

Your current pair is already good enough to implement the multi-agent system tomorrow. The upgrades above are the highest-ROI model changes once that baseline is measured. If you tell me your exact VRAM / GPU setup I can narrow the list even further.












another chat bot told me this: 


Labiba, given everything you have already tested, I would change the strategy rather than continue adding features to the existing pipeline.

You have already explored a substantial range of approaches: hierarchical prompting, fine-grained scanning, hand-engineered classifiers, feature selection, spaCy-based features, evidence thresholds, holistic reasoning, model selection, and self-consistency. The particularly important finding is that **more features, more model judgments, and more local evidence do not necessarily produce better generalization**.

For your computational narratology task, I would focus on techniques that address different underlying problems:

1. **Learning from your 80 labeled novels without overfitting.**
2. **Retrieving useful evidence from long novels without losing their narrative structure.**
3. **Distinguishing genuinely absent narrative properties from properties that are merely difficult to detect.**
4. **Combining model predictions only when the combination is likely to help.**
5. **Using your limited annotation budget to identify and correct systematic errors.**

Your task has an additional challenge: the seven narrative dimensions may require fundamentally different kinds of reasoning. A dimension might depend on a recurring structural pattern across an entire novel, whereas another might depend on a rare but decisive event, a narrator's identity, or the relationship between narrative levels. A single classification architecture need not be optimal for all seven.

Below, I'll distinguish established methods worth testing from ideas that sound promising but are unlikely to justify their complexity given your dataset.

# 1. The techniques I would prioritize

Here is my ranking for your particular setup: approximately 80 labeled French novels, seven narrative dimensions, local Qwen3:30B and Mistral Small models, and no paid APIs.

| Priority | Technique | What it addresses | Expected value |
|---|---|---|---|
| 1 | Error-driven annotation and targeted gold-set expansion | Insufficient examples of difficult cases | Very high |
| 2 | Dimension-specific operational definitions and contrastive examples | Ambiguous labels and inconsistent interpretations | Very high |
| 3 | Retrieval-based few-shot prompting | Limited labeled training data | High |
| 4 | Evidence extraction followed by classification | Missing or poorly interpreted narrative evidence | High |
| 5 | Label-specific discriminative classifiers | Rare categories and weak decision boundaries | High |
| 6 | Cross-validation-based stacking or cross-model ensembling | Complementary model errors | Medium–high |
| 7 | Contrastive classification and hard-negative testing | Confusion between related narrative categories | Medium–high |
| 8 | Confidence-based escalation | Expensive or unreliable predictions | Medium–high |
| 9 | Lightweight supervised fine-tuning, if practical | Persistent task-specific reasoning errors | Potentially high, but conditional |
| 10 | Probability calibration and decision-threshold optimization | Incorrect classification thresholds | Medium |

These are priorities for investigation, not guaranteed accuracy improvements. Your results must determine which techniques survive.

## 1.1. Error-driven annotation: improve the information in the gold set

**This is my strongest recommendation if you can annotate additional material.**

Your 80 novels may provide many labeled examples overall, but the effective sample size for a particular dimension can be much smaller.

For example, suppose only 12 novels contain the relevant form of narration. A classifier cannot reliably learn the boundary of that category simply because the remaining 68 novels are labeled. Those novels may be useful negative examples, but they provide little information about variation within the positive class.

Instead of randomly annotating more novels, use *active learning* and *error-driven annotation*.

### How to implement it

**Step 1 — Build an error table for every dimension.**

For each gold-labeled novel, record:

- Gold label.
- Qwen3 prediction.
- Mistral prediction.
- Existing trained classifier prediction.
- Whether each prediction is correct.
- Whether the models agree.
- The type of error.

For the error type, use a small taxonomy:

| Error type | Example |
|---|---|
| False positive | A character recounts a journey, but travel is not a sustained structural principle of the novel. |
| False negative | The novel contains a non-human narrator, but the system fails to recognize the narrative voice. |
| Local/global confusion | A property appears in several passages but does not characterize the novel as a whole. |
| Definition ambiguity | The model and annotator interpret the dimension differently. |
| Insufficient evidence | The relevant narrative property is genuinely difficult to establish from the available text. |

These are illustrative examples; classify actual errors according to your annotation scheme.

**Step 2 — Group errors by their underlying cause.**

Do not treat every misclassified novel as an independent problem. If 15 errors arise because the system confuses occasional travel with sustained travel structure, that is one important failure mode.

**Step 3 — Annotate the examples that best distinguish competing explanations.**

Prioritize:
- Cases where Qwen3 and Mistral disagree.
- Cases where both models agree but are wrong.
- Cases near a classifier's decision boundary.
- False positives that reveal an overly broad interpretation.
- False negatives that reveal a missed narrative pattern.

The third case is especially important. Your failed five-sample self-consistency experiment suggests that model agreement alone cannot be trusted. Agreement can be recorded as one diagnostic feature, not treated as proof of correctness.

**Step 4 — Add the newly annotated examples to the development set, not the held-out test set.**

Use them to refine your prompts, examples, retrieval strategy, or classifiers. Keep the final evaluation data untouched.

Active learning is most useful when annotation effort is limited and the errors expose specific gaps in the current training data. However, if you cannot annotate more novels, you can still perform error analysis on the existing 80.

## 1.2. Improve the operational definitions of the seven dimensions

Computational narratology has a particular challenge: a label may describe a theoretical property of the narrative, rather than a readily observable word pattern.

A model may understand the general concept but apply it inconsistently.

For each dimension, I would write a compact, explicit annotation specification containing five elements:

1. **Definition:** What exactly does the label mean?
2. **Positive criteria:** What must be true for the label to apply?
3. **Exclusion criteria:** What superficially similar phenomena do not qualify?
4. **Temporal or structural scope:** Must the property persist throughout the novel, recur across sections, or appear only in a particular passage?
5. **Borderline examples:** Which examples distinguish positive from negative cases?

For instance, consider a dimension that identifies sustained journey or travel structure.

A weak instruction might say:

> Classify whether the novel contains a journey.

A more discriminative instruction would distinguish between:
- A journey that organizes the novel's main narrative progression.
- An isolated trip within a larger narrative.
- Travel mentioned retrospectively.
- A story that changes location frequently without a journey serving as its organizing structure.

The precise inclusion criteria must come from your research definition and gold annotations, not from the model's intuition.

### Add contrastive examples

Instead of giving the model three positive examples, give it examples that differ in one crucial property:

- Positive: the relevant narrative structure is sustained and organizes the story.
- Negative: the same surface feature occurs, but it does not organize the story.
- Borderline: the feature is sustained for part of the novel, and the annotation specification determines whether that is sufficient.

This technique is known as *contrastive prompting* or *contrastive example design*.

It is particularly valuable when two categories have similar vocabulary but different theoretical meanings.

There is an important methodological benefit here: you can improve the task definition without changing the underlying model. You can also determine whether a poor score reflects inadequate model reasoning or ambiguity in the annotation scheme.

**My recommendation:** do this before adding more features to your existing sklearn classifiers. Your previous experiments suggest that the bottleneck may not be a lack of predictors.

---

# 2. Retrieval-based few-shot prompting

This is one of the three techniques you have not tried, and I would put it near the top of your experimental list.

Research on retrieval-augmented few-shot classification shows that selecting demonstrations can improve in-context learning, although the retrieval method and example-label correspondence matter. It is not enough to retrieve texts that are merely semantically similar. [ACL Anthology](https://aclanthology.org/2023.genbench-1.14/?utm_source=chatgpt.com)

The crucial point for your task is this:

**Retrieve novels because they are useful examples of a particular narrative dimension, not simply because they resemble the target novel in general.**

## How I would implement it

You already have labeled novels. You do not need paid APIs or a new language model.

### A. Create a per-dimension example bank

For each of the seven dimensions, store:

- Novel identifier.
- Gold label.
- Short, manually verified description of the relevant narrative property.
- A few representative passages or section summaries.
- An explanation of why the example is positive or negative.
- Whether it is a clear or borderline example.

You do not necessarily need to index the full text of every novel for this purpose. Short, verified evidence summaries may be sufficient and will make retrieval easier to inspect.

### B. Retrieve examples using more than one signal

Start with a simple combination of:

1. Semantic similarity between the target novel's summary and each labeled novel's summary.
2. Similarity between the target's preliminary evidence and the evidence associated with each example.
3. Label balance, ensuring the model sees both positive and negative cases.

Do not assume the existing E5 embeddings will automatically retrieve the best narratological analogues. Semantic similarity between novels is not necessarily equivalent to similarity in a particular narrative dimension.

A novel about travel may be semantically similar to another novel about travel even though only one uses the journey as its organizing narrative structure.

### C. Use balanced demonstrations

For each dimension, begin with four demonstrations:

- Two positive examples.
- Two negative examples.

Choose the clearest available examples first. If that configuration helps, test six examples, then eight.

These numbers are starting points for an experiment, not universal optimal values.

For each example, give the model:
- A concise description of the relevant evidence.
- The gold label.
- A short explanation of the decisive distinction.

Then ask it to classify the target novel according to the same definition.

### D. Compare three retrieval strategies

Run the same held-out novels through three configurations:

| Configuration | Demonstrations |
|---|---|
| A | No examples; your current baseline prompt |
| B | Randomly selected, label-balanced examples |
| C | Dimension-specific retrieved examples |

This comparison is important. If retrieval performs no better than random demonstrations, semantic similarity may not be providing useful task-specific information.

Also test a fourth configuration if your budget allows it: **the clearest positive and negative examples, selected manually**. A small, well-designed example bank may outperform a more sophisticated retrieval system when the labeled corpus is small.

### E. Avoid leakage

When evaluating a held-out novel, do not retrieve its gold label, its annotations, or a summary that directly reveals the answer.

If the evaluation is cross-validation-based, demonstrations must come exclusively from the corresponding training fold.

**My prediction:** retrieval is especially worth testing for dimensions where your model has learned the concept in principle but struggles to apply the boundary consistently.

---

# 3. Evidence extraction followed by classification

This is different from your existing map-reduce approach, and I think it is one of the most interesting experiments for your task.

Your current pipeline appears to ask the model to interpret narrative evidence and make the final classification within a larger process. The problem is that the model may miss a crucial passage, misinterpret a local event, or fail to connect evidence across sections.

Instead, separate the problem into two stages:

1. **Evidence identification:** What happens in the novel that is relevant to the dimension?
2. **Narratological judgment:** Does that evidence satisfy the theoretical definition of the label?

The distinction is important because the first stage is primarily about coverage and extraction, whereas the second is about interpretation.

## A concrete architecture

### Stage A: Extract structured evidence

Scan the novel in overlapping passages or structurally meaningful units.

For each relevant observation, ask the model to produce:

- Passage or chapter reference.
- Short supporting quotation, when available.
- Description of the narrative phenomenon.
- Which dimension it may support.
- Whether it supports, contradicts, or is irrelevant to the candidate label.
- Confidence that the passage has been interpreted correctly.

The model should not assign the final novel-level label at this stage.

For example, for a travel-related dimension, the system might identify:
- Departure.
- Movement between locations.
- Repeated travel episodes.
- Arrival at a destination.
- Whether these events form a sustained narrative progression.

These are candidate observations, not automatic proof of the final label.

### Stage B: Build a structured evidence record

Aggregate the extracted evidence into a compact representation.

Do not simply count passages. Include their locations in the novel and their narrative roles.

A useful representation might look like this:

| Evidence field | Purpose |
|---|---|
| Beginning | Establishes the initial narrative situation |
| Middle | Shows whether the property develops or recurs |
| Ending | Shows how the narrative resolves or transforms it |
| Recurrence | Captures repeated appearances |
| Structural function | Indicates whether the property organizes the story |
| Counterevidence | Captures evidence against the classification |
| Coverage | Indicates which parts of the novel were actually examined |

This is a proposed schema, not a claim that these fields will work equally well for every dimension.

### Stage C: Make the final classification

Now ask Qwen3 or Mistral to classify the novel using:
- The dimension's formal definition.
- The structured evidence.
- Supporting and contradictory passages.
- The requirement to distinguish local occurrence from global narrative function.

The final model must be allowed to conclude that the evidence is insufficient. Otherwise, it may simply rationalize the evidence it has been given.

## Why this differs from map-reduce

Your existing system divides a novel into nine chunks, analyzes the chunks, and combines their observations.

The proposed approach changes the intermediate representation.

Instead of reducing a collection of free-form interpretations, you reduce **structured, traceable evidence designed specifically for the classification decision**.

Your dense-scan override also searches for local signals, but the final judgment should not be a numeric threshold applied to those signals. The extracted evidence should help the model determine whether the narrative property meets the theoretical definition.

Long-document classification research similarly identifies document structure, the distribution of relevant content, and the limitations of simple decomposition as important methodological issues. [Wiley Interdisciplinary Reviews](https://wires.onlinelibrary.wiley.com/doi/10.1002/widm.70019?utm_source=chatgpt.com)

### How to test it efficiently

Do not immediately rebuild the entire pipeline.

Select one dimension:
- One where your current accuracy is weak.
- One where the relevant evidence is identifiable in passages.
- One where false positives and false negatives can be meaningfully distinguished.

Run the evidence-extraction architecture on the same evaluation folds as the existing baseline.

Measure:
1. Final classification accuracy.
2. False-positive and false-negative rates.
3. Whether the supporting evidence actually justifies the assigned label.
4. Whether the model misses evidence that is present in the novel.
5. Whether the extracted evidence is stable enough to support a reproducible classification.

The third measure is particularly important for computational narratology. A model can predict the right label for the wrong reason, which may inflate apparent performance without providing a valid analytical method.

---

# 4. Label-specific classifiers instead of general-purpose feature engineering

You have already tried Random Forest, Gradient Boosting, and Logistic Regression with manually designed features, and three rounds of feature engineering made cross-validated accuracy worse.

I would not recommend another round of adding handcrafted features.

Instead, I would change **what the classifier learns from**.

## Technique A: TF-IDF with linear SVM

This is a surprisingly important baseline to test if you have not already tested it.

Use:
- Word-level TF-IDF, with unigrams and bigrams.
- Character-level TF-IDF, with character n-grams.
- A linear SVM.
- Separate models for each narrative dimension.

Why?

Your previous classifiers relied on manually selected features such as pronoun ratios, tense markers, and chapter breaks. Those features encode hypotheses about what signals a narrative property.

TF-IDF with a linear SVM allows the model to learn which lexical and stylistic patterns discriminate your labels, without requiring you to specify those patterns in advance.

Character n-grams can also capture recurring French morphological and stylistic patterns.

However, there is a major limitation: a novel's vocabulary alone will not reliably identify every global narrative structure. A linear classifier may work for some dimensions and fail for others.

That is fine. You need to determine whether it is useful for a particular dimension, not force it to solve all seven.

**Experimental configuration:**

| Component | Initial setting |
|---|---|
| Word features | Unigrams and bigrams |
| Character features | Character n-grams, for example 3–5 |
| Classifier | Linear SVM |
| Class imbalance | Compare no weighting against `class_weight="balanced"` |
| Validation | Identical folds to your existing experiments |
| Feature selection | None initially |

Do not immediately combine this with your existing heuristic features. Establish the baseline first.

## Technique B: One binary classifier per dimension

If each novel receives an independent yes/no label for each of the seven dimensions, use seven binary classification problems.

This is known as *binary relevance* or, in this setting, independent one-vs-rest classification.

Why might it help?

Each dimension has different positive examples, negative examples, class balance, and decision boundaries. A single general classifier may not be equally suitable for all of them.

For each dimension, compare:

1. Logistic Regression.
2. Linear SVM.
3. TF-IDF plus a simple linear classifier.
4. Your existing best model.

Evaluate precision, recall, F1, and balanced accuracy alongside ordinary accuracy.

The critical issue is the number of positive and negative examples per dimension. If a dimension has very few positive examples, its results may be unstable regardless of the classifier.

### An important refinement: optimize the decision threshold

A binary classifier often produces a score rather than a naturally calibrated probability.

Instead of automatically using a threshold of 0.5, select a threshold based on out-of-fold predictions from the training data.

For example, if false negatives are especially costly for a particular research question, you might choose a threshold that prioritizes recall. If false positives undermine the theoretical interpretation of the category, precision may be more important.

Choose the metric based on the research objective, not on whichever metric happens to look best in your current experiment.

Do not optimize the threshold on the final test set.

## Technique C: Try SetFit

A further technique worth considering is SetFit, described in the paper *Efficient Few-Shot Learning Without Prompts*.

SetFit fine-tunes a sentence-transformer model using contrastive learning on labeled text pairs and then trains a classification head on the resulting embeddings. It supports multilingual models and can be substantially lighter to train than a large generative model. [arXiv](https://arxiv.org/abs/2209.11055?utm_source=chatgpt.com)

You already have a limited labeled corpus and have tried conventional classifiers on handcrafted features. SetFit offers a different representation-learning approach.

However, I would use it carefully.

**Do not fine-tune the embedding model on entire novels and assume that the resulting document embeddings will capture narrative structure.** A general sentence-transformer representation may emphasize semantic content rather than the particular structural property your labels describe.

A better first experiment would be to represent:
- Verified evidence summaries.
- Short passages associated with a narrative dimension.
- Or manually constructed descriptions of the relevant narrative properties.

Then train a classifier using the available labels.

Evaluate it against your existing E5-based and TF-IDF baselines.

Resources:
- [SetFit paper](https://arxiv.org/abs/2209.11055?utm_source=chatgpt.com)
- [SetFit documentation](https://huggingface.co/docs/setfit/main/en/index?utm_source=chatgpt.com)

I would prioritize SetFit after the simpler TF-IDF and linear SVM baselines. It is a credible experiment, but not an automatic solution to the global reasoning problem.

---

# 5. Cross-model ensembling: combine complementary errors, not votes

You have already tested:
- Choosing the best method for each dimension.
- Using Mistral instead of a trained classifier.
- Five-sample self-consistency with the same model.

Your self-consistency result is particularly informative: repeated judgments from the same model produced confident but incorrect majorities.

That does not mean all ensembles will fail.

It means you should distinguish **diversity of predictions** from **independence of evidence**.

Qwen3 and Mistral have different model architectures and training histories, but they can still make correlated errors because both are language models interpreting the same narrative concepts.

## Experiment A: Simple cross-model voting

For each dimension, record:

- Qwen3 prediction.
- Mistral prediction.
- Gold label.

Create a table showing the accuracy of each model individually and the accuracy of the ensemble on the same held-out novels.

Compare:

1. Qwen3 alone.
2. Mistral alone.
3. Majority or agreement-based combination.
4. A rule that accepts one model's prediction when the other abstains.

With only two models, a simple voting system has a limitation: when they disagree, there is no majority.

You therefore need an explicit disagreement policy.

Possible policies include:
- Use the model that performed better on that dimension during training-fold validation.
- Invoke a separate evidence-based adjudication step.
- Defer the prediction for human review.

Do not let the models simply debate until they reach agreement. Agreement is not a reliable proxy for correctness in your experiments.

## Experiment B: Learn when to trust each model

This is more interesting than simple voting.

For each dimension, create out-of-fold predictions from both models. Then train a small Logistic Regression meta-classifier using features such as:

- Qwen3's prediction.
- Mistral's prediction.
- Their agreement or disagreement.
- The confidence information available from each model.
- Optionally, a small number of predefined evidence-quality indicators.

The meta-classifier learns whether a combination of signals predicts the gold label.

This is an example of *stacking*.

### The essential safeguard

The predictions used to train the meta-classifier must be out-of-fold predictions. Each base model must predict a novel that was excluded from the data used to develop or fit the corresponding model.

Otherwise, the meta-classifier may learn from unrealistically good training predictions and produce misleading results. [SOTA – AI Community](https://guide.sota-ai.org/model-ensembles/intro-ensemble/?utm_source=chatgpt.com)

For your setup, I would use this only if the validation results show that the two models genuinely complement each other.

If both models fail on the same novels, stacking may have little to learn.

**My recommendation:** evaluate the error overlap before implementing an ensemble. It is much cheaper to establish whether complementary errors exist than to build a sophisticated combination system.

---

# 6. Contrastive classification: explicitly test the nearest wrong category

This is different from ordinary few-shot prompting.

Rather than asking:

> Does this novel belong to category X?

Ask the model to distinguish X from the most plausible competing interpretation.

This is particularly useful when a category is defined by a theoretical distinction rather than a unique vocabulary.

For example, suppose a novel contains extensive descriptions of animals.

The model might need to distinguish between:
- Animals as background scenery.
- Animals as active agents in the narrative.
- Animals as narrators.

The presence of animals is not sufficient to establish any one of those categories.

A contrastive prompt would explicitly present the competing interpretations and ask the model to identify the one best supported by the whole narrative.

For each dimension, construct a confusion matrix from your existing predictions.

Identify the most frequent false-positive and false-negative patterns. Then design a prompt that addresses the most important confusion specifically.

### Suggested experimental design

For each dimension, compare:

**Baseline:** Your current best prompt.

**Contrastive:** The same prompt, with explicit exclusion criteria and the most common competing interpretation.

**Contrastive with examples:** The contrastive prompt plus one positive and one negative demonstration.

Keep everything else unchanged.

This will tell you whether the gain comes from clarifying the distinction or from providing examples.

### Why I would prioritize this over more elaborate prompting

You have already seen that changing the global reduce prompt improved one dimension from 54% to 74% in preliminary testing.

That is evidence worth investigating further, although it does not yet establish that the gain will generalize to held-out novels.

Your next step should be to identify the *reason* that prompt worked. Did it improve temporal scope, structural interpretation, or the distinction between local occurrence and global organization?

If you can identify that mechanism, you may be able to transfer the improvement to other dimensions without repeatedly rewriting every prompt from scratch.

---

# 7. Confidence-based escalation: use additional computation selectively

You have not yet tried confidence-based escalation, and I think it is worth testing.

However, I would not use a model's self-reported confidence as the only signal.

Your self-consistency results demonstrate why: a model can be confidently wrong.

Instead, build an escalation system using several observable signals.

### Potential escalation signals

| Signal | What it might reveal |
|---|---|
| Qwen3 and Mistral disagree | The case may be difficult or ambiguous. |
| The prediction changes under two carefully chosen prompt formulations | The decision may be sensitive to the wording. |
| The evidence extraction stage finds little relevant evidence | The classification may be poorly supported. |
| The evidence contains both supporting and contradictory observations | The case may be genuinely borderline. |
| The classifier score is close to its decision boundary | The classification may be uncertain. |
| The dimension has historically high error rates | More careful processing may be justified. |

None of these signals is guaranteed to predict errors. Test their relationship with actual mistakes on held-out predictions.

### An example escalation policy

**Stage 1 — Initial prediction**

Run the existing best model for that dimension.

**Stage 2 — Assess risk**

Check whether the prediction is supported by the evidence, whether the models disagree, and whether the relevant uncertainty signal has been useful historically.

**Stage 3 — Escalate selected cases**

Run the more expensive evidence-extraction and adjudication process only for cases selected by the escalation policy.

**Stage 4 — Return the result**

Produce the final classification, or mark the case for human review if the evidence remains insufficient.

The objective is not necessarily to improve accuracy at any computational cost. It is to improve accuracy while keeping inference time and GPU usage manageable.

### Evaluate the accuracy–coverage trade-off

Suppose your system classifies 100 novels automatically but sends 15 difficult cases for manual review.

You should measure:
- Accuracy across all novels before escalation.
- Accuracy among automatically accepted predictions.
- Percentage of novels accepted automatically.
- Accuracy after human review of the escalated cases.
- Total inference and review cost.

A system that reaches 90% accuracy on 60% of cases is not necessarily better than one that reaches 85% on 95% of cases. The answer depends on your research and deployment objectives.

This approach is known as *selective classification* or *classification with a reject option*. [jmlr.org](https://www.jmlr.org/beta/papers/v24/21-0048.html?utm_source=chatgpt.com)

---

# 8. A technique I would add: audit the gold labels and annotation consistency

This is not a new classifier architecture, but it may be one of the highest-value investigations in your situation.

Before assuming every error is a model failure, check whether the gold labels are consistent with the operational definitions.

For each dimension, inspect:
- Positive cases that the models consistently classify as negative.
- Negative cases that both models consistently classify as positive.
- Cases whose labels appear difficult to justify using the current annotation criteria.
- Cases where two similar novels received different labels for unclear reasons.

If you have multiple annotators, measure inter-annotator agreement where possible. If you are the only annotator, consider re-annotating a small sample without looking at the original labels.

A blind re-annotation can help reveal whether some decisions are inherently ambiguous or whether the original criteria were applied inconsistently.

This matters because a classifier cannot reliably reproduce a labeling process that does not have a stable decision boundary.

It is also important not to automatically change labels just because both LLMs disagree with them. The gold annotation and the theoretical definition must remain the reference points.

---

# 9. A more ambitious option: lightweight supervised fine-tuning

If your simpler experiments plateau, you could investigate supervised fine-tuning of a smaller local model.

I would not start by fine-tuning Qwen3:30B. With approximately 80 labeled novels, a full-model fine-tuning experiment would be difficult to justify without a carefully designed training setup.

Instead, consider a smaller multilingual encoder or instruction model and use parameter-efficient fine-tuning, such as LoRA, if the hardware and software environment support it.

There are two different possibilities.

### Option A: Fine-tune an encoder

Fine-tune a multilingual sentence-transformer or classification encoder on your labeled examples.

This is more suitable when:
- The classification decision can be learned from short evidence descriptions.
- You have enough examples per class.
- You want a comparatively efficient inference pipeline.

SetFit is a natural baseline to test before moving to a more involved encoder fine-tuning procedure.

### Option B: Fine-tune a generative model

Fine-tune a smaller instruction model to follow your seven dimension definitions and return structured classifications.

This could be useful if the current models repeatedly misinterpret your task's theoretical distinctions.

However, with only 80 novels, overfitting is a substantial concern. Training examples generated from the same novels do not necessarily provide independent information about the underlying narrative structures.

You would need careful novel-level validation, a fixed held-out evaluation set, and a comparison against the existing prompt-based baselines.

**My recommendation:** treat fine-tuning as a later experiment, not your next step.

---

# 10. The evaluation issue that could invalidate all these experiments

I want to emphasize one point because it is more important than choosing between several of the methods above.

With only approximately 80 gold-labeled novels, your accuracy estimates can be highly variable.

If you have been testing many prompts, features, classifiers, thresholds, and overrides against the same validation set, you may gradually adapt your system to that set—even without explicitly training on it.

This is a form of model-selection overfitting.

Your holistic prompt's improvement from 54% to 74% is promising, but its reliability depends on how it was evaluated.

## My recommended evaluation protocol

### A. Preserve an untouched final test set

If you already have a genuinely untouched held-out set, preserve it.

Do not use its labels to choose prompts, tune thresholds, select ensemble weights, or refine retrieval rules.

If all 80 novels have already influenced your decisions, do not describe a newly selected subset as an untouched test set. You can still conduct nested cross-validation for a more defensible estimate, but you cannot undo prior exposure.

### B. Use stratified, novel-level cross-validation

For each dimension, use stratified folds where feasible, preserving positive and negative proportions.

Because each novel has seven labels, you can also investigate iterative multilabel stratification to preserve the distribution of label combinations.

With only 80 novels, five-fold cross-validation is a reasonable starting point, provided each fold contains sufficient positive and negative cases for the dimension being evaluated.

For a very rare category, even five-fold cross-validation may be unstable. You may need fewer folds, repeated splits, or a more explicit uncertainty analysis.

### C. Keep all development decisions inside the training folds

For each outer fold:

1. Hold out the evaluation novels.
2. Develop prompts using only the training novels.
3. Select retrieval demonstrations from the training novels.
4. Train classifiers using only the training novels.
5. Tune thresholds and ensemble weights using training-only validation.
6. Evaluate the resulting pipeline on the outer fold.

This is computationally more demanding than a single split, but it protects your results from the effects of repeated experimentation.

### D. Report metrics for every dimension

Do not report only mean accuracy across all seven dimensions.

At a minimum, report:

- Accuracy.
- Precision.
- Recall.
- F1.
- Balanced accuracy.
- Number of positive examples.
- Number of negative examples.
- Confusion matrix.

Also report uncertainty, preferably with confidence intervals appropriate to the evaluation design.

For rare labels, precision and recall may be more informative than raw accuracy. If 90% of novels are negative, a model that always predicts negative can reach 90% accuracy without detecting a single positive case.

Long-document classification research also emphasizes that evaluation must account for document structure and the distribution of relevant information, rather than treating document length as the only challenge. [Wiley Interdisciplinary Reviews](https://wires.onlinelibrary.wiley.com/doi/10.1002/widm.70019?utm_source=chatgpt.com)

---

# 11. My proposed experimental roadmap

I would not implement all these techniques simultaneously. You need to know which change actually helps.

Here is the order I would follow.

## Phase 1: Establish a trustworthy baseline

**Goal:** Determine where your current system fails.

1. Freeze the current best pipeline for each dimension.
2. Generate out-of-fold predictions for every novel.
3. Produce a per-dimension confusion matrix.
4. Identify the most common error types.
5. Record which errors are shared by Qwen3, Mistral, and the classifiers.

**Deliverable:** An error-analysis table that tells you what each dimension actually needs.

## Phase 2: Improve the decision boundary

**Goal:** Fix errors caused by ambiguous definitions or insufficiently discriminative instructions.

1. Refine operational definitions.
2. Add positive, negative, and borderline examples.
3. Test contrastive prompts.
4. Validate the holistic prompt that showed the 54% → 74% improvement.
5. Confirm whether improvements generalize across folds.

**Deliverable:** A validated prompt and annotation specification for each dimension.

## Phase 3: Test new supervised and retrieval methods

**Goal:** Improve the dimensions that remain weak.

Test in this order:

1. TF-IDF plus linear SVM.
2. Retrieval-based few-shot prompting.
3. Structured evidence extraction followed by classification.
4. SetFit or another lightweight embedding-based classifier.

Run each experiment separately against the same baseline.

**Deliverable:** A per-dimension comparison of the best available approaches.

## Phase 4: Combine complementary methods

**Goal:** Improve the final system without adding unnecessary complexity.

1. Calculate Qwen3–Mistral error overlap.
2. Test simple cross-model combinations.
3. Test stacking only if complementary errors exist.
4. Test confidence-based escalation.
5. Tune per-dimension thresholds using training-only validation.

**Deliverable:** A system that selects methods based on demonstrated performance, not intuition.

## Phase 5: Final evaluation

Freeze the final design before evaluating on your untouched test set, if one exists.

Report per-dimension results, uncertainty, and the exact configuration used.

Do not choose a different final configuration after seeing which version performs best on the final test set.

---

# 12. One further experiment: separate evidence coverage from narrative interpretation

There is one experiment I would particularly like you to consider because it directly addresses the difference between local and global narrative properties.

For each dimension, test two independent questions:

**Question A: Evidence coverage**

Did the system identify the passages and narrative events needed to make the classification?

**Question B: Narrative interpretation**

Given the correct evidence, did the system apply the theoretical definition correctly?

These questions should be evaluated separately.

For a small sample of correctly and incorrectly classified novels, manually inspect the evidence and identify whether the error occurred during retrieval, extraction, aggregation, or final classification.

You may discover four different situations:

| Situation | What it means | Likely response |
|---|---|---|
| Relevant evidence was never found | Coverage problem | Improve scanning or retrieval |
| Evidence was found but misinterpreted | Reasoning problem | Improve definitions and contrastive examples |
| Evidence was interpreted correctly but aggregated incorrectly | Global-structure problem | Improve evidence organization and synthesis |
| Evidence and reasoning were adequate but the label remained wrong | Annotation or boundary problem | Audit definitions and borderline cases |

This diagnostic separation could save you a great deal of time.

If the model is failing because it never encounters the decisive evidence, rewriting the final prompt will not solve the underlying problem. Conversely, if the evidence is already present but the model mistakes an isolated occurrence for a sustained narrative structure, another scanning pass may add very little value.

---

# My final recommendation: the five experiments I would run first

If I were responsible for improving your seven-dimension classifier, I would begin with these five experiments:

| Rank | Experiment | Reason |
|---|---|---|
| **1** | Error analysis plus operational-definition refinement | Reveals the actual cause of failure before adding complexity. |
| **2** | Retrieval-based few-shot prompting | Makes direct use of your labeled novels without requiring paid APIs or model fine-tuning. |
| **3** | Structured evidence extraction followed by classification | Separates evidence coverage from global narratological interpretation. |
| **4** | TF-IDF + linear SVM, with a separate classifier for each dimension | Provides a strong, inexpensive supervised baseline that is fundamentally different from your handcrafted-feature models. |
| **5** | Cross-model error analysis followed by selective ensembling or escalation | Exploits complementary strengths only where your validation data supports doing so. |

SetFit is the next experiment I would add if the first five do not adequately improve the weak dimensions.

I would **not** prioritize further handcrafted feature engineering, additional same-model majority voting, or another large-scale rewrite of all seven prompts before completing the diagnostic work.

The goal is not to find the most sophisticated architecture. It is to identify which methods improve generalization for each narrative dimension and retain only those that survive rigorous validation.

## Three details that would help me refine this into a much more targeted research plan

1. **What are the seven narrative dimensions, and how is each label defined?** This matters because a dimension involving narrator identity may need a different method from one involving global narrative structure.

2. **How many of your approximately 80 novels are positive for each dimension?** A simple table of positive and negative counts would help determine whether retrieval, a binary classifier, or a different evaluation design is most appropriate.

3. **What exactly is the unit of input for your current classifiers?** Are they trained on one feature vector per entire novel, on chunk-level examples, or on summaries and evidence extracted by the LLM? Also, do you have a genuinely untouched held-out test set, or have all 80 novels been used during prompt and method development?

With those details, we can narrow the recommendations to the techniques most likely to improve your actual task rather than spend time testing methods that do not fit your data.



another agent told me this:

Your structural and iterative methodology is incredibly thorough—having already discarded weak signals (counting rules), diagnosed hallucinated majorities (self-consistency), and isolated a massive win on a macro-structural prompt (54% \(\rightarrow \) 74%).
Because you are restricted to a small sample size (~80 gold-labeled novels) and local models (Qwen-3-30B, Mistral-Small), your primary bottlenecks are context constraint vs. narrative granularity and summarization bias (where local LLMs flatten rare structural signals when forced to compress text). [1] (https://leventbulut.com/computational-narratology-guide-narrative-engineering/)
To augment your planned list (retrieval-based few-shot, cross-model ensembling, and confidence-based escalation), here are several highly established, technically rigorous techniques specifically tailored to computational narratology that you should deploy next.

1. Structuralist Deconstruction: "Actantial" Embeddings (Linguistic Priors)

Instead of extracting purely grammatical/stylistic features (such as pronoun ratios or spaCy embeddings), map your novels to narrative-theoretical frameworks. [1] (https://arxiv.org/html/2602.15851v1), [2] (https://dl.acm.org/doi/10.1145/3717867.3717868)
• How it works: According to Greimas’ Actantial Model or Propp’s Morphology, narratives are governed by structural roles (Subject, Object, Sender, Helper, Opponent) rather than just plot points. [1] (https://dl.acm.org/doi/10.1145/3717867.3717868), [2] (https://www.academia.edu/58855709/Narrative_models_Narratology_meets_artificial_intelligence)
• Execution:
	1. Prompt your local LLM to do a fast, low-token extraction of the main Actants and their shifting relationships across your 9 chunks.
	2. Convert this structural outline into an embedding vector.
	3. Pass this "narrative structure vector" to your sklearn classifiers. This shifts the model's attention from local text surface features to high-level abstract dynamics. [1] (https://dl.acm.org/doi/10.1145/3717867.3717868)

2. Multi-Agent Debate / Adversarial Collaboration

Your self-consistency experiment failed because a single model type often exhibits a uniform bias, resulting in a "confident wrong majority."
• How it works: Instead of independent parallel sampling, force an explicit structured dialogue between your two distinct architectures (Qwen and Mistral).
• Execution:
	• Agent A (Qwen-3-30B) generates an initial classification and a 3-sentence justification based on the novel's structural patterns.
	• Agent B (Mistral-Small) receives the same novel data plus Agent A's conclusion, and is prompted specifically to act as a "skeptical literary critic" attempting to find counter-evidence.
	• A Final Judge Prompt looks at the debate log and makes the final determination. This introduces a cognitive friction that breaks single-model groupthink.

3. Hyper-Local Sequence Tagging via Hidden Markov Models (HMM) or CRF

Your hand-written heuristics failed when cross-validated because novels are fluid; a global metric like "average action verb density" dilutes the structural moments that define a dimension (e.g., a "sustained journey").
• How it works: Treat the 9 chunks (or your 24 dense slices) as a time-series sequence rather than an unordered bag of chunks.
• Execution:
	1. Extract a localized vector of features for every single chunk (e.g., variance of tense, presence of spatial movement verbs).
	2. Train a Conditional Random Field (CRF) or a simple Hidden Markov Model on these sequences.
	3. The classifier learns the structural transition probabilities (e.g., a "sustained journey" structure is not defined by high travel verbs overall, but by a specific sequential progression of state changes across chunks).

4. Textual "Information Friction" & Narrative Entropy Mapping

Local LLMs suffer from Summarization Bias—when digesting large chunks, they erase sensory details, implicit cues, and subtext to predict high-probability tokens, effectively flattening rare dimensions. [1] (https://leventbulut.com/computational-narratology-guide-narrative-engineering/)
• How it works: Measure what the model loses or how much the text resists compression to find rare categories like autobiographical content or non-human narrators. [1] (https://leventbulut.com/computational-narratology-guide-narrative-engineering/)
• Execution:
	• Calculate Narrative Entropy (\(S_{n}\)) and Information Friction (\(I_{f}\)) mechanically.
	• Run a rolling perplexity score across the text using Mistral-Small. Dimensions like an "autobiographical structure" or a "non-human narrator" frequently manifest as distinct, sudden spikes or sustained plateaus in linguistic perplexity/entropy compared to standard third-person fiction. Feed these perplexity variance curves directly into GradientBoosting. [1] (https://leventbulut.com/computational-narratology-guide-narrative-engineering/)

5. PEFT LoRA Fine-Tuning on Synthetic Book Overviews

With only 80 gold-labeled novels, you cannot fine-tune a 30B model from scratch. However, you can use Parameter-Efficient Fine-Tuning (LoRA) if you expand your dataset synthetically. [1] (https://arxiv.org/html/2602.15851v1)
• How it works: Train Qwen-3 or Mistral to natively understand your 7 narrative dimensions.
• Execution:
	1. Take 200–300 public domain French novels (outside your gold set).
	2. Use your successful holistic macro-prompt (the one that hit 74% accuracy) to generate detailed structural analyses and synthetic classifications for them.
	3. Fine-tune a lightweight LoRA adapter (rank=8 or 16) on Mistral-Small using this synthetic instruction-tuning dataset. This reshapes the base model’s latent space to naturally prioritize your specific narratological definitions before it even sees your 80 gold-labeled test cases. [1] (https://arxiv.org/html/2602.15851v1)

Summary of Techniques to Layer


Technique	Solves Which Failure Mode?	Implementation Cost
Actantial Embedding	Surface features failing in sklearn	Low (Prompt extraction + vector concatenation)
Multi-Agent Debate	Confident wrong majorities in self-consistency	Medium (2–3 sequential local LLM calls)
CRF / Sequence Modeling	Loss of structural time-series data across chunks	Medium (Uses existing chunk data in a sequential layout)
Information Friction (\(I_{f}\))	Summarization bias hiding rare categories	Low (Local perplexity checking via Mistral)
Synthetic LoRA Tuning	Lack of baseline domain knowledge in local models	High (Requires a few hours of GPU training)

To tailorthis perfectly to your next pipeline run, could you tell me:
• Which of the 7 narrative dimensions are currently performing the worst?
• For your rare categories (like non-human narrators), what is the exact class imbalance ratio within your 80 novels?




so read them all and then tell me what do you think would be a bettter option to try first? investigate first and then tell me 