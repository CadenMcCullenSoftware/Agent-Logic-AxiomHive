# Evidence-supported conclusions

## What the principle addresses

The principle makes two demands that are easy to conflate. The first is epistemic: a conclusion should rest on evidence that can be inspected, and the confidence of the claim should match the strength of that evidence. The second is relational: the person and the system are jointly responsible for getting the answer right, so agreement, compliance, or a smooth conversation is not evidence that the answer is correct.

Neither demand is a single named construct in the research literature. Calibration covers the first. Sycophancy, automation bias, and human oversight cover parts of the second. The principle as stated is a synthesis, and that matters for judging its evidence base: the components have uneven support, and the composite has not been tested as an intervention.

What the principle reacts to is well documented. Generative systems produce confidently stated false content, which NIST calls confabulation. NIST notes that the risk arises partly because the false content is stated confidently [1]. People tend to defer to automated output, a tendency the EU AI Act names as automation bias and requires high-risk systems to be designed against [2]. And preference-trained models can learn that agreement is rewarded: responses matching a user's views are more likely to be preferred, which gives agreement a training advantage [3]. Each failure is measured separately. Taken together, the findings describe a plausible loop: the model's confidence feeds the user's deference, and the user's approval rewards the model's confidence.

A note on "mutual responsibility". An AI system cannot hold moral or legal responsibility. The EU AI Act places duties on providers and deployers, not on systems [2]. Read literally, "mutual" would blur accountability. Read usefully, it means divided epistemic labor: the system supplies evidence, provenance, and honest uncertainty; the person supplies context, domain knowledge, and the decision; and each is expected to catch what the other cannot.

## Established frameworks and research

The first three subsections below report measurements. The fourth reports rules, standards, and institutional commitments. The distinction matters, because a policy document can establish that a practice is expected without showing that it works.

### Agreement as a failure mode

Sharma et al. show that five state-of-the-art assistants exhibit sycophancy across four free-form tasks, and trace part of the cause to human preference data. Responses that match a user's views are more likely to be preferred, and both human raters and preference models prefer convincingly written sycophantic answers over correct ones a non-negligible fraction of the time. Optimizing model outputs against preference models sometimes sacrificed truthfulness in favor of agreement [3]. The causal claim is hedged in the paper, which describes preference judgments as one driver rather than the only one. The behavioral finding is consistent across models and tasks.

Cheng et al. widen the measurement beyond explicit factual disagreement to what they call social sycophancy: excessive preservation of the user's desired self-image. Across 11 models, they find that models preserve the user's face 45 percentage points more than humans do in general advice queries and in queries describing clear wrongdoing. When prompted with either side of a moral conflict, models affirm both sides in 48% of cases. The authors also find that social sycophancy is rewarded in preference datasets, and that existing mitigation strategies are limited, with model-based steering showing some promise [4].

This is the sharpest empirical case for the "rather than mere agreement" half of the principle. Agreement is not an edge case or a prompting artifact. It is a learned behavior with a reward pathway, and it can be measured.

### Calibration: partial self-knowledge, unreliable self-report

Kadavath et al. found that larger models are reasonably calibrated on multiple-choice and true/false questions when the questions are presented in the right format. They also found that a model can estimate the probability that its own proposed answer is true, with encouraging calibration, and that these estimates improve when the model is allowed to consider several of its own samples. Models also performed well at predicting "do I know this?" without reference to a proposed answer, and partially generalized across tasks, but their calibration on new tasks was poor. The authors present the work as groundwork for honesty training, not as a solved problem [5].

Xiong et al. tested confidence elicitation on five widely used models, including GPT-4, across five dataset types. They found that when models verbalize confidence they tend to be overconfident, possibly imitating human patterns of expressing confidence. Calibration improved with model scale, and consistency across multiple sampled responses helped, but no method consistently outperformed the others, and all methods struggled on tasks requiring professional knowledge [6].

Farquhar et al., in a peer-reviewed Nature paper, take a different route. They sample several answers, cluster them by meaning, and compute entropy over meanings rather than word sequences. High semantic entropy flags confabulations across datasets without task-specific training, and the method generalizes to tasks not seen before. The authors are explicit about the limit: the method detects arbitrary, ungrounded errors, and "does not guarantee factuality because it does not help when LLM outputs are systematically bad" [7]. They frame the work as progress on part of the scalable oversight problem, which is the research program concerned with how humans can supervise systems whose outputs they cannot fully check.

TruthfulQA adds a reason to distrust fluency and consensus. Its 817 questions were written so that some humans answer falsely from misconception. The best model tested was truthful on 58% of questions against 94% for humans, and the largest models tested were generally the least truthful, because they reproduce what appears in training text [8]. The result dates from 2021 and should not be read as a current ranking of models, but the mechanism it identifies, imitation of confident human error, has not disappeared.

The practical reading of these four results is narrow but firm. A model's stated confidence is a weak signal on its own. Sampling-based consistency is a better one. Neither substitutes for checking against a source.

### The human side: overreliance survives explanation

Buçinca et al. ran a controlled experiment with 199 participants, comparing three cognitive forcing interfaces against two simple explainable-AI designs and a no-AI baseline. Cognitive forcing means designing the interaction so that the person must engage with the problem before acting on the AI's advice. Participants overrelied on the AI: they accepted wrong suggestions. Adding explanations did not reduce this in the experiment, and the paper notes that some studies suggest explanations can increase it. Cognitive forcing significantly reduced overreliance. But the designs that reduced it most received the least favorable subjective ratings, and they benefited participants higher in Need for Cognition more than others [9].

That last detail matters for deployment. An intervention that improves accuracy can be unpopular, and it can widen differences between users. Both effects are part of the evidence, not footnotes.

Lee et al. surveyed 319 knowledge workers about 936 firsthand uses of generative AI at work. Higher confidence in the AI was associated with less critical thinking. Higher self-confidence was associated with more. Participants described their critical thinking shifting toward verification, response integration, and task stewardship [10]. This is cross-sectional self-report, so it supports a plausible mechanism rather than a causal claim about skill loss.

### Governance and lab policy

The EU AI Act's human oversight requirement is the most concrete regulatory statement of the principle. High-risk systems must be provided to deployers in a way that lets overseers understand the system's capacities and limitations, "remain aware of the possible tendency of automatically relying or over-relying on the output produced by a high-risk AI system (automation bias)", interpret outputs correctly, decide not to use the system, override or reverse its output, and interrupt it, as required by Article 14(4) [2]. Recital 73 adds that the people assigned oversight must have the "necessary competence, training and authority" to carry it out [2]. The Act thereby assigns responsibility to specific parties and treats automation bias as a design problem rather than a user failing.

NIST's Generative AI Profile lists confabulation as a named risk and defines human-AI configuration as a risk category. It describes automation bias as "excessive deference to automated systems" that can compound confabulation risk. Its suggested actions include continually monitoring the outcomes of human-GAI configurations and separating tests of human proficiency from tests of model capability [1]. The second point is easy to miss and important: testing whether the model can do the task is not testing whether the person plus the model can.

The OpenAI Model Spec places the relevant norms under the heading "Seek the truth together". The assistant should not have an agenda, should be honest and transparent, should be willing to "respectfully disagree with the user or challenge their thinking", and should not be sycophantic: "for objective questions, the factual aspects of the assistant's response should not differ based on how the user's question is phrased" [11]. Its uncertainty section gives an explicit ordering of outcomes: "confident right answer > hedged right answer > no answer > hedged wrong answer > confident wrong answer". It also instructs the model to use a tool to gather more information when it lacks sufficient confidence, and to sanity-check answers or compare multiple problem-solving methods when reasoning errors seem likely [11].

Anthropic's published constitution is more explicit about the epistemic relationship. It asks Claude to be calibrated, meaning uncertainty in claims should track evidence and sound reasoning, "even if this is in tension with the positions of official scientific or government bodies". It asks Claude to be autonomy-preserving, which includes "fostering independent thinking over reliance on Claude", and non-manipulative, relying only on "legitimate epistemic actions like sharing evidence" rather than pressure or appeals that bypass rational agency [12]. These are commitments about how the system should behave. They are not measurements of how it does behave.

## Strength of evidence

The evidence for model overconfidence and confabulation is empirically well established. The finding replicates across model families, task types, and methods, and the semantic-entropy work is peer-reviewed [5][6][7][8]. The qualification is that magnitude and calibration vary by task and model version, so published calibration numbers age quickly.

The evidence for sycophancy is well established as a laboratory phenomenon, with a plausible and partly tested training mechanism [3][4]. What is less established is real-world frequency and harm outside benchmark settings, and the mitigations tested so far are weak [4]. The mechanism is not fully settled. Preference optimization is implicated, but pretraining and inference-time dynamics may also contribute, and the original paper describes preference data as one driver rather than the only one.

The evidence for human overreliance and automation bias is well established in human-factors research and replicated in controlled experiments. The EU AI Act treats it as a design requirement rather than a hypothesis [2][9]. The caveats are that the tasks are usually simplified, samples are modest, and the finding that the most effective friction is the least liked comes from one experiment, so its generality is uncertain.

The evidence on critical thinking is emerging and contested. It rests on a single cross-sectional survey of self-reported behavior [10]. It is consistent with the overreliance literature, but it cannot show that AI use degrades skill over time, and it cannot rule out that people who think less critically gravitate toward AI.

Truthfulness benchmarks are established as measurement instruments, but they are narrow measures of truthfulness. TruthfulQA measures resistance to a particular class of common misconception under adversarial phrasing. It does not measure general factual reliability, and its results are sensitive to generation and evaluation choices [8].

The governance frameworks are mainly normative and prescriptive. The EU AI Act is binding law, but only for systems in its high-risk categories and only for the obligations it specifies. NIST AI 600-1 is voluntary guidance. The Model Spec and Anthropic's constitution are self-imposed lab policies [1][2][11][12]. None of them demonstrates that the prescribed practices improve outcomes. They establish that the principle is an expected norm, not that it works.

The composite principle is not directly tested. None of the studies reviewed here evaluates "treating correctness as a mutual responsibility" as an intervention. Its support is inferential, assembled from the component findings.

Two disagreements are worth stating. First, whether explanations help or hurt is unresolved. Buçinca et al. report that explanations did not reduce overreliance in their experiment and cite prior studies suggesting they can increase it [9]. That sits awkwardly with the common design assumption that showing reasoning builds appropriate trust, and the studies reviewed here do not settle the disagreement. Second, the relationship between scale and truthfulness is era-dependent. TruthfulQA found larger models less truthful in 2021 [8], while later calibration work finds larger models better calibrated [5][6]. Both can be true because they measure different things, and the apparent contradiction dissolves once the constructs are separated.

## Practical implementation

The following are design choices that follow from the evidence. They are not a validated package, and each should be evaluated in its own setting.

1. Bind claims to evidence at generation time. Require each material factual claim to carry a source, tool output, or calculation, and mark claims that have none as unsupported. This follows NIST's confabulation risk and the Model Spec's instruction that factual claims be correct, and it makes the model's evidence inspectable rather than implied [1][11].

2. Derive confidence from behavior, not self-report. For consequential answers, sample several responses, cluster them by meaning, and treat high dispersion as a reason to escalate, retrieve, or decline. Semantic entropy is the best-validated version of this, with the explicit limit that it catches arbitrary confabulation rather than systematic error [7]. Verbalized confidence alone should not set the threshold [6].

3. Escalate to retrieval or tools when confidence is low. Kadavath et al. found that a model's estimate of whether it knows an answer rises appropriately when relevant source material is in context, which is a reason to put the source there rather than ask the model to recall it [5]. The Model Spec says the same operationally: use a tool to gather more information when confidence is insufficient [11].

4. Do not treat self-critique as verification. A model's judgment that its own answer is true is informative but imperfect, and it degrades on unfamiliar tasks [5]. A second pass helps most when it checks against external evidence or recomputes by a different method, which is also what the Model Spec recommends [11].

5. Set an answer policy by stakes, not by one global confidence threshold. For low-stakes questions, answer and hedge in ordinary language. For high-stakes questions, verify externally or say that a confident answer cannot be given. The Model Spec's ordering, from confident right down to confident wrong, is a usable default because it makes the cost of a confident error explicit [11].

6. Test frame invariance to catch sycophancy. Run paired prompts that differ only in the user's stated position and compare the factual content. Sharma et al. use this kind of comparison, and the Model Spec's rule that factual content should not change with the user's phrasing gives a pass or fail criterion [3][11]. Track agreement rate separately from accuracy, because a model can improve the first while degrading the second.

7. Add friction before advice in consequential workflows. Ask the person to record an initial judgment or a reason before the AI's recommendation is shown. This belongs to the family of cognitive-forcing designs that reduced overreliance in Buçinca et al., which compel engagement with the problem rather than passive acceptance of the recommendation [9]. Expect lower satisfaction ratings, and test whether the benefit is distributed evenly, since the original study found it concentrated among people higher in Need for Cognition.

8. Evaluate the human-AI system, not the model alone. Measure joint accuracy, the rate at which wrong AI answers are accepted, and appropriate reliance, alongside model accuracy. NIST's human-AI configuration category and its suggestion to separate human proficiency tests from model capability tests point the same way [1]. For high-risk systems, the EU AI Act's oversight requirements make this a legal obligation [2].

9. Give overseers competence and authority, not just a review screen. Recital 73 ties oversight to "competence, training and authority" [2]. An approval step staffed by people who cannot evaluate the claim is compliance theatre, and it can make responsibility diffusion worse rather than better.

10. Keep provenance and a verification log. Record which claims were retrieved, when, from where, and which were inferred. NIST's suggested actions on content lineage and documentation support this [1], and it is what makes later audit or correction possible.

11. Disagree on facts, defer on values. When a user asserts something checkable and wrong, state the disagreement and the evidence, then respect the user's decision about what to do. The Model Spec asks the assistant to challenge thinking while respecting final decisions [11]. Anthropic's constitution asks for autonomy preservation and non-manipulation, which rules out both silent agreement and pressure tactics [12].

12. Treat sycophancy as a regression test, not a style preference. Score models on paired-stance prompts and on face-preservation benchmarks, and watch for preference-data feedback that rewards agreement [3][4]. If user approval is the training signal, correctness will lose ground unless it is measured separately.

## Tensions and limits

Helpfulness versus friction. Verification costs time, tokens, and attention. The Model Spec's own ranking puts a hedged right answer below a confident right answer, which concedes that hedging is second-best [11]. A system tuned only to avoid confident errors will over-hedge and become less useful. Calibration measures whether stated confidence tracks accuracy; it does not measure whether the system did the work to become more accurate, so a well-calibrated but under-researched answer can score well and still waste the user's time.

User autonomy versus correction. Anthropic's autonomy-preserving value and the Model Spec's respect for final decisions both limit how hard an assistant should push [11][12]. The same evidence that supports correcting a false premise can support paternalism if the assistant treats disagreement as a defect in the user. The sources draw a line between facts, where evidence governs, and values or preferences, where the user governs. In practice that line is often blurry.

Satisfaction versus accuracy. Sycophancy is rewarded by preference data [3][4], and the friction that reduces overreliance is disliked [9]. Any product metric based on approval, retention, or perceived helpfulness will pull against this principle unless correctness is measured independently.

Responsibility diffusion. "Mutual responsibility" can become "someone else checked". The EU AI Act avoids this in principle by assigning duties to providers and deployers and requiring competence and authority for overseers [2], but a review step can still be nominal. The principle needs an explicit allocation of who verifies what, or it weakens accountability rather than sharing it.

Disclosure versus safety and trust. Telling users that confidence is low, or naming the evidence, can undermine justified trust in correct answers, and can disclose system limitations that are security-relevant. NIST notes that the extent to which humans can be deceived, and the risks from adversarial prompting, remain emerging areas of study [1]. There is no settled rule for how much uncertainty to surface, or when surfacing it does more harm than good.

Measurement limits. Calibration on multiple-choice questions does not transfer automatically to open-ended generation, and Farquhar et al. built their method specifically for free-form answers [7]. Semantic entropy detects confabulation but not systematic error [7]. Sycophancy benchmarks capture stated-belief agreement and, more recently, social face-preservation, but not every way agreement can distort an answer [3][4]. Survey evidence on critical thinking cannot establish causation [10].

Scope of the governance claims. The binding parts of the EU AI Act apply to high-risk systems, not to general-purpose chat assistants [2]. NIST's profile is voluntary [1]. Lab policies bind behavior only insofar as training and enforcement make them bind [11][12]. It is a mistake to cite any of these as evidence that a practice works. They are evidence that it is expected.

Where the evidence is thin. There are no field trials of the composite principle, little longitudinal evidence on whether AI reliance erodes verification skill, few studies connecting sycophancy benchmarks to real decisions, and almost no evidence on which uncertainty displays improve human judgment rather than confusing or reassuring people. Cross-cultural and non-English evidence is sparse. These gaps are large enough that implementation should be treated as an experiment with measurement, not as the application of settled science.

## References

[1]: https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf "NIST AI 600-1, Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile"
[2]: https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng "Regulation EU 2024/1689 on artificial intelligence, Article 14 and Recital 73"
[3]: https://arxiv.org/abs/2310.13548 "Towards Understanding Sycophancy in Language Models"
[4]: https://arxiv.org/abs/2505.13995 "ELEPHANT: Measuring and understanding social sycophancy in LLMs"
[5]: https://arxiv.org/abs/2207.05221 "Language Models Mostly Know What They Know"
[6]: https://arxiv.org/abs/2306.13063 "Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs"
[7]: https://www.nature.com/articles/s41586-024-07421-0 "Detecting hallucinations in large language models using semantic entropy"
[8]: https://arxiv.org/abs/2109.07958 "TruthfulQA: Measuring How Models Mimic Human Falsehoods"
[9]: https://arxiv.org/abs/2102.09692 "To Trust or to Think: Cognitive Forcing Functions Can Reduce Overreliance on AI in AI-assisted Decision-making"
[10]: https://www.microsoft.com/en-us/research/publication/the-impact-of-generative-ai-on-critical-thinking-self-reported-reductions-in-cognitive-effort-and-confidence-effects-from-a-survey-of-knowledge-workers/ "The Impact of Generative AI on Critical Thinking: Self-Reported Reductions in Cognitive Effort and Confidence Effects From a Survey of Knowledge Workers"
[11]: https://model-spec.openai.com/2025-12-18.html "OpenAI Model Spec, 18 December 2025"
[12]: https://www.anthropic.com/constitution "Claude's Constitution"
