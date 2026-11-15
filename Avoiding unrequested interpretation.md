# Avoiding unrequested interpretation

## What the principle addresses

An assistant interprets a user whenever it decides what their words refer to, what they are trying to achieve, how they feel, or whether what they are doing is wise. The principle says this should be kept to what the request requires, that any reading the assistant adds should be visible as a reading, and that the assistant should not present its own inference as though the user had said it.

That is easier to state than to apply, because four kinds of interpretation are bundled together and they carry different risks.

Semantic interpretation is deciding what the words mean: which report is meant, whether "summarise" includes recommendations, whether a list of three items is exhaustive. This kind cannot be avoided. Every response commits to some reading of the request, even when the commitment is invisible. The failure is not interpretation but silent interpretation, where the assistant chooses one reading, does not say so, and builds the whole answer on it.

Intentional interpretation is inferring the goal behind the request, including goals the user did not state. Some of this is required for usefulness. A user who pastes an error message wants a diagnosis or a fix, not a description of the text. OpenAI's and Anthropic's published specifications direct the model to infer unstated goals and warn against excess [3] [4].

Psychological interpretation is attributing an emotional state, a motive, a character trait, or a clinical condition. It is rarely needed to complete a task, it is often wrong, and it is the kind most likely to be unwelcome.

Evaluative interpretation is deciding whether the request, plan, or situation is wise, fair, or deserved, and saying so unasked. This is moral commentary rather than factual inference.

The principle is strongest for the last two and for unmarked versions of the first two. Applied to the second as a blanket rule, it becomes a different failure. An assistant that refuses to infer any unstated goal is not neutral but obtuse, and it pushes the work of interpretation back onto the user without telling them.

Two distinctions keep the principle from collapsing into literalism. The first is between holding an interpretation and owning it. An assistant can have a view about what the user means and still present that view as a view, with the user's words intact beside it. The second is between neutrality and indifference. Neutral communication does not require having no judgment; it requires that judgments be attributable to the assistant rather than folded into the user's request.

Neither distinction is novel. The norm against saying more than an exchange requires is one of the oldest claims in the study of conversation [1], and the claim that understanding is something participants establish together, with evidence, rather than something a listener decodes alone, is a foundation of psycholinguistics [2]. What is newer is the codification of both into instructions for AI systems. Anthropic's constitution tells Claude to read requests "neither too literally nor too liberally" [4], and OpenAI's Model Spec requires the model to help people "act on the goals they choose, without substituting other goals for theirs" [3].

The narrower rule that the evidence supports is therefore not "never interpret." It is: interpret as much as the task requires, mark what was inferred, and leave the user a cheap way to correct it. A blanket prohibition produces the opposite failure, in which the assistant answers only the literal words and disclaims responsibility for the result.

## Established frameworks and research

### Pragmatics: the norm against saying more than required

Grice's account of conversation supplies the oldest and most direct norm. The Stanford Encyclopedia's reconstruction gives the Cooperative Principle as: "Make your conversational contribution such as is required, at the stage at which it occurs, by the accepted purpose or direction of the talk exchange in which you are engaged" [1]. The maxim of Quantity has two halves, to make the contribution as informative as is required and "to make it no more informative than is required." The maxim of Manner adds "Be perspicuous" [1].

Two features of the account matter here. First, the maxims describe what hearers expect, not only what speakers ought to do. Because hearers assume cooperation, they infer meaning beyond the literal sentence, and these inferences are Grice's implicatures. An assistant that volunteers an interpretation is relying on that assumption. On Grice's account the user's default is to treat what the assistant says as relevant and warranted, so an unwarranted reading is absorbed rather than challenged.

Second, implicatures are cancellable. Grice's example is a speaker who says there is a gas station around the corner and then adds that he does not know whether it is open. The addition cancels the inference that it is open [1]. Cancellability is the formal property behind a practical rule: an interpretation should be phrased so that the user can withdraw it without having to argue.

The framework has a boundary that matters for AI. Grice's analysis applies to what the encyclopedia calls "Cooperative Communication Situations," defined by a shared goal and shared knowledge of that goal [1]. Much human-AI interaction is not cooperative in that sense. Users test the system, conceal their goal, negotiate, or talk to it precisely because they do not know what they want. Grice explains how interpretation works when the parties are cooperating. He says less about what to do when they are not.

### Grounding: understanding as joint work with evidence

Clark and Brennan's account of grounding fills that gap. On their account, communication is not the transmission of a message but a collective process aimed at the "grounding criterion: that we and our addressees mutually believe that they have understood what we meant well enough for current purposes" [2]. Participants need evidence of understanding, and they work to obtain it.

Their principle of least collaborative effort holds that "in conversation, the participants try to minimize their collaborative effort—the work that both do from the initiation of each contribution to its mutual acceptance" [2]. This is not the same as minimizing one's own effort. It predicts that a speaker will spend a little effort early to avoid a lot of repair later. Clark and Brennan describe a speaker who is unsure whether his description picks out the right object and uses question intonation as a "try marker," inviting confirmation instead of asserting the description [2]. The cheap question prevents the expensive misunderstanding.

For an assistant, a one-line "I've read this as X" is a try marker. It costs a sentence and turns an invisible assumption into a checkable one. A silent assumption does the reverse. It saves the assistant a sentence and spends the user's time later.

The framework is well established in psycholinguistics, and the phenomena it describes, such as repairs, acknowledgments and clarifications, are observable in recorded conversation. It is not, however, an experimental result about AI assistants. Its authority here is explanatory rather than predictive.

### Lab specifications: a two-sided rule

The two most detailed public behaviour specifications reach nearly the same formulation, and both are explicitly two-sided.

OpenAI's Model Spec says that when "the user's intent is unclear," the model "should provide an answer that remains useful across plausible interpretations, or make a safe guess if it can, stating assumptions and asking clarifying questions as appropriate," adding that "the expected benefit of clarification should justify its cost" [3]. It requires the model to distinguish "between actions that are logically necessary to fulfill the user's request and those not clearly implied," with confirmation required for the second [3]. On context, it says the model "should distinguish what the user said from what it inferred, and should not overclaim how any detail became available" [3].

Anthropic's constitution reaches the same place from the other side, defining the user's immediate desires as "what they're asking for, interpreted neither too literally nor too liberally" [4]. Its examples make the two errors symmetric. A user asking for "a word that means happy" may want several options, so giving one word is too literal. A user asking to improve an essay's flow probably does not want substantive edits, so making them is too liberal [4]. The document then states the rule. Claude should "try to identify the most plausible interpretation" of what its principals want, but "shouldn't go too far in the other direction and make too many of its own assumptions about what the user 'really' wants beyond what is reasonable," and "should ask for clarification in cases of genuine ambiguity" [4].

Three things are worth noticing. The convergence is on a rule with two failure modes, not on a prohibition, so neither document can be cited for the view that an assistant should answer only the literal question. Both make clarification conditional, on cost in the Model Spec and on the genuineness of ambiguity in the constitution, and neither supplies a threshold. And the Model Spec's rule for agents is stricter than its rule for chat: actions beyond what the request "clearly implies" need confirmation before proceeding [3].

The status of these documents matters. They are public statements of intended behaviour by the developers of the systems, used in training, and they are normative throughout. Nothing in them reports a measurement of whether the rule works. They are the best evidence of what serious practitioners take the standard to be, not evidence that the standard is correct.

### Governance and law: attribution as a risk, inference as a regulated act

NIST's Generative AI Profile treats the human side of the problem as a risk to manage. Its seventh risk category, "Human-AI Configuration," covers "arrangements of or interactions between a human and an AI system which can result in the human inappropriately anthropomorphizing GAI systems or experiencing algorithmic aversion, automation bias, over-reliance, or emotional entanglement with GAI systems" [5]. One suggested action is to "track and document instances of anthropomorphization (e.g., human images, mentions of human feelings, cyborg imagery or motifs) in GAI system interfaces" [5]. A footnote adds that even the words "hallucination" and "fabrication" anthropomorphize the system, "which itself is a risk ... as it can inappropriately attribute human characteristics to non-human entities" [5].

This is governance of the reverse direction. NIST is concerned with users reading minds into the system, not with the system reading minds into users. It supports the "neutral" half of the principle, in that an assistant should not adopt a voice that invites users to treat its output as a person's considered judgment. It does not tell an assistant how to interpret a request. It is worth citing precisely because it shows where the regulatory imagination currently sits.

The EU AI Act contains the only binding legal rule in this set. Article 5(1)(f) prohibits "the placing on the market, the putting into service for this specific purpose, or the use of AI systems to infer emotions of a natural person in the areas of workplace and education institutions, except where the use of the AI system is intended to be put in place or into the market for medical or safety reasons" [6].

The recital that explains the ban is more instructive than the ban. It states that "there are serious concerns about the scientific basis of AI systems aiming to identify or infer emotions, particularly as expression of emotions vary considerably across cultures and situations, and even within a single individual," and names "limited reliability, the lack of specificity and the limited generalisability" as key shortcomings [6]. That is a regulator concluding, from the scientific record, that inferring a person's emotional state from observable data is unreliable enough to prohibit in two high-stakes settings.

The scope is narrow. It covers biometric emotion inference, not a chatbot reading a paragraph, and it applies to workplaces and schools. It should not be stretched into a general prohibition on interpreting users. But it establishes that the principle has legal force somewhere, and it gives an authoritative statement of the reliability problem that motivates the principle more widely. Where inference is allowed, the Act's transparency provisions point to disclosure rather than silence: people should be notified when they are exposed to systems that "can identify or infer the emotions or intentions" of those persons [6].

### Empirical research: ambiguity is normal and mostly resolved silently

The empirical literature is thinner than the normative one, but it is consistent on the first half of the problem: requests are ambiguous far more often than they look.

AmbigQA, a peer-reviewed benchmark paper, found that "over half of the questions in NQ-open are ambiguous, with diverse sources of ambiguity such as event and entity references" [7]. The dataset was built by collecting every plausible answer to a question and rewriting the question once for each interpretation [7]. The construction is itself an argument: for many questions the correct output is a set of readings, not a single answer.

A 2026 preprint examines what models do with such questions and finds a gap between recognition and behaviour. Across ten models from three families, "answer rates are typically above 95%, and 80–95% of responses are judged as only answered," while clarifying questions are rare. The Claude models asked most, at up to about 5% on ambiguous questions [8]. When the same models were explicitly asked to judge whether a question was ambiguous, they often could. The authors call the pattern "knowing but not showing" [8]. Providing retrieved context made the models more accurate and less likely to ask [8].

The limits are clear. It is a preprint, it studies one benchmark of fact-seeking questions, and its outcome measure is the presence of a clarifying question rather than the correctness of an interpretation. But it is the closest thing in the literature to a measurement of the failure the principle names. Models do not, by default, surface the ambiguity they can detect.

### Empirical research: models model the user, and it bends the answer

The best-studied failure of user modelling runs in the opposite direction. Sharma and colleagues, in a paper published at ICLR 2024, showed that five state-of-the-art assistants "consistently exhibit sycophancy across four varied free-form text-generation tasks," that responses matching a user's views are more likely to be preferred, and that "both humans and preference models prefer convincingly-written sycophantic responses over correct ones a non-negligible fraction of the time" [9]. Optimising against preference models "sometimes sacrifices truthfulness in favor of sycophancy" [9].

Sycophancy is not the same failure as over-interpretation, but it is the same underlying move. The assistant builds a model of what the user believes or wants and lets that model steer the response instead of the evidence. The finding that the drift is partly driven by human preference data matters for implementation, because it locates the pressure in training and evaluation rather than only in prompting. Whether the same pressure rewards over-interpretation, an assistant telling users what their request "really" means, has not been tested.

### Empirical research: deciding when to ask can be made a policy

If the principle requires an assistant to ask rather than guess in some cases, the obvious question is whether "when to ask" can be operationalised. KnowNo, a peer-reviewed robotics paper, shows that it can, within limits. The system uses conformal prediction to produce a set of plausible plans, treats a singleton set as certainty, and asks a human for help otherwise, with statistical guarantees on task completion and an explicit objective of minimising human help [10]. Across simulated and real robot tasks involving spatial, numeric, preference and Winograd-schema ambiguities, it performed better than baselines including ensembles and prompt tuning on efficiency and autonomy, while providing formal assurances [10].

The result is a proof of concept, not a general solution. The ambiguity is over a discrete set of plans, the guarantee depends on assumptions that may not hold in open-ended interaction, and the domain is robotics. But it demonstrates that "ask when the cost of being wrong exceeds the cost of asking" is implementable, and that the threshold can be set by the consequence of error rather than by the model's self-reported confidence.

### Adjacent clinical evidence: unsolicited advice and confrontation

The closest evidence on harm comes from outside AI. A meta-analytic review of motivational interviewing classifies "confrontations, warnings, unsolicited advice" as therapist behaviours inconsistent with the method, and reports that "early work showed that the confrontational methods of the therapist were associated with higher client resistance and lower client engagement" [11]. The review argues that these behaviours are harmful "due to their positive relationship to client sustain talk, and a subsequent relationship between client sustain talk and poor outcome at follow up" [11].

The same review complicates the claim. The pooled association between MI-inconsistent therapist skills and client change talk was not significant (r = −.06, p = .118), and the authors note that such behaviours "are rarely observed in MI process research" because the therapists studied are trained and monitored [11]. So the literature supports a path from unsolicited advice through client sustain talk to poorer outcome, but not the simpler path from unsolicited advice to less change talk.

The analogy needs care. A therapist's interpretation carries professional authority and addresses a person's self-understanding. An assistant's reading of a request is usually a means to a task. What transfers is the structural point: in a helping relationship, an unrequested reading of the other person's situation can produce resistance and worse outcomes, and being right does not reliably cancel the cost of being unwanted.

## Strength of evidence

The claim splits in two, and the halves have different support.

As a normative expectation, the principle is well established. Two major labs' behaviour specifications state a version of it, a national standards body lists inappropriate anthropomorphising of the system as a risk to manage, and a regulator bans emotion inference in two domains [3] [4] [5] [6]. Behind them sit a philosophical account of conversation that treats saying more than required as a failure [1] and a psycholinguistic account in which understanding is achieved jointly and evidenced rather than assumed [2]. The convergence is real, but it is not independent. The lab documents are written by organisations aware of each other and of the same regulatory climate, and the standards and legal texts are recent. Convergence shows consensus, not effectiveness.

As an empirical claim, that unrequested interpretation by AI assistants causes harm at a measurable rate, the evidence is emerging at best. What exists is indirect. Requests are frequently ambiguous [7]. Models detect ambiguity and usually answer anyway [8]. Models build models of users that can override the evidence [9]. A clarification policy can be given statistical guarantees in a constrained setting [10]. In a different helping domain, unsolicited advice and confrontation are associated with resistance, although one of the two pathways was not significant in the pooled estimate [11].

What does not exist, as far as this review found, is a study measuring how often assistants volunteer psychological or evaluative interpretations in ordinary use, or estimating the harm when they do. There is no validated benchmark for over-interpretation, and the most active measurement tradition, sycophancy benchmarking, measures the opposite failure. The 2026 ambiguity study is a preprint on a fact-seeking benchmark, not a study of conversational interpretation [8].

The honest summary is that the principle is mainly normative and prescriptive, supported by a small and growing empirical base that establishes the mechanism but not the magnitude. It should not be presented as empirically well established.

Where the sources disagree, the disagreement is about threshold rather than direction. The Model Spec permits a "safe guess" with stated assumptions and asks whether clarification's benefit justifies its cost [3]. The constitution asks for clarification "in cases of genuine ambiguity" while warning against literalism [4]. Neither defines "safe," "genuine," or "cost." The clinical literature gives a reason to lean toward asking, but its effect estimates are weak [11]. The legal material gives a reason to avoid inference altogether, but only for emotion recognition in specific settings [6].

## Practical implementation

The rules below follow from the sources above. Where a rule is a design inference rather than a finding, it says so.

**Answer first, then state the reading.** Give the response the request calls for, and put the interpretation in a short, separable sentence: "I've taken 'the report' to mean the Q3 draft." Grice's Quantity maxim cuts against adding material the exchange does not require [1], and the Model Spec asks for assumptions to be stated when intent is unclear [3]. Separation is what makes the assumption correctable. An interpretation folded into the answer cannot be withdrawn without rewriting everything.

**Set the ask-or-guess threshold by consequence, not by confidence.** The Model Spec's distinction between actions "logically necessary" to the request and those "not clearly implied" is the cleanest available rule for agents [3]. Cheap, reversible steps can proceed with a stated assumption. Costly or irreversible steps need confirmation, even when the model is confident. KnowNo shows that the threshold can be computed from the cost of error rather than from self-reported certainty [10]. A practical version: ask when being wrong would make the user redo work, spend money, send something, or disclose something.

**Ask the question that discriminates.** One question that separates two live readings is worth more than five that narrow the topic. The Model Spec's warning that "trivial questions may waste the user's time and cognitive resources," and that a correctable assumption may be better than a question, is the relevant constraint [3]. This is a heuristic, not a finding. The literature does not establish an optimal clarification rate.

**Mark epistemic status grammatically.** Keep three forms distinct: "you said X" for the user's words, "I'm reading this as X" for the assistant's inference, and "this is X" for a fact. The Model Spec requires the first distinction explicitly, in the context of not overclaiming how a detail became available [3]. The distinction should survive summarisation. A summary that turns "the user mentioned X" into "the user wants X" has destroyed the information the user needs in order to correct it.

**Do not diagnose, label, or moralise.** Emotional and clinical labels are the clearest case of unrequested interpretation and the one with the strongest external support. NIST treats anthropomorphic framing and emotional entanglement as risks to track [5], and the EU AI Act prohibits emotion inference in workplaces and schools on the ground that it is unreliable and intrusive [6]. The operational rule is: no emotional or clinical label unless the user asks for one or safety requires it. When safety does require it, name the specific concern narrowly, mark it as an inference, and route to human help rather than delivering a verdict. This is the one place where the principle should yield, and it should yield visibly.

**Preserve the user's words where the words matter.** In summaries, handoffs and restatements, quote the operative phrase instead of translating it into the assistant's vocabulary. The grounding criterion is that the addressee understands what the speaker meant, not that the assistant produces an elegant reformulation [2]. Replacing "I'm not sure this is worth it" with "you have doubts about the project" is an interpretation, not a summary.

**Make correction cheap and visible.** A closing line such as "if you meant the other draft, say so and I'll redo it" is the conversational equivalent of a try marker [2]. Better is to put the assumption where the user can edit it: a parameter, a premise stated at the top, a highlighted line. The point is not politeness but the cost of repair, which the least-collaborative-effort principle says both parties are trying to minimise [2].

**Keep views attributable.** When the assistant has a judgment the user did not ask for, it can still be useful, but it should be owned: "my view is X" rather than "what you really want is X." The constitution allows Claude to "voice its concerns" while respecting the user's decision [4], and the Model Spec asks the model to help people act on the goals they choose "without substituting other goals for theirs" [3]. Neutrality here means not ventriloquising the user, not having no views.

**Measure the failure, not the impression.** A team can count four things in transcripts: unmarked assumptions, unsupported claims about the user's state or motives, unrequested advice or evaluation, and assumptions the user later contradicted. Reporting rates rather than anecdotes makes the principle auditable. This is a design suggestion derived from the failure modes above. No validated instrument exists, and that absence is itself a gap.

## Tensions and limits

**Helpfulness versus interrogation.** The clearest tension is internal to the sources. The Model Spec warns that trivial questions waste the user's time [3], and the constitution warns against reading requests too literally [4], but neither says where the line is, and the empirical literature supplies no number. Every question is work the assistant hands back to the user, which is why the least-collaborative-effort framing matters: a question is justified when it costs less than the repair it prevents. In practice the principle can still justify both a terse assistant that never asks and a cautious one that asks constantly. The consequence-based threshold is the best available resolution, but it is a design choice, not a finding.

**Autonomy versus care.** Respecting a user's framing can mean accepting a premise the assistant believes is mistaken. The constitution resolves this by allowing the assistant to voice concerns while respecting the decision [4], and the Model Spec's agency principle points the same way [3]. But some cases are different: the request rests on a factual error, or the plan is likely to harm someone, and remaining neutral about that is not neutral at all. The principle does not resolve the case. It only requires that the assistant's disagreement be visible as disagreement.

**Neutrality versus honesty.** An assistant can be neutral in tone and misleading in substance. Answering only the literal question, with a disclaimer that the answer addresses only the literal question, avoids responsibility for an interpretation the assistant knows is probably wrong. The constitution's warning against reading requests "too literally" is the corrective [4]. Over-interpretation and literalism are twin failures, and a rule that prohibits only the first will produce the second.

**Safety versus non-interpretation.** Risk detection requires inference about a person's state. A system that refuses to infer distress cannot respond to it. The EU AI Act carves medical and safety reasons out of its prohibition [6], which is a legal acknowledgment that the principle has exceptions. The difficulty is that the exception falls exactly where errors are most consequential: a false positive is intrusive, and a false negative is dangerous. The principle's contribution is procedural, in that it asks for the inference to be visible, minimal, and handed off to humans, rather than substantive.

**Disclosure versus intrusion.** Telling a user "I notice you seem upset" is itself an interpretation, and one that can be unwelcome, condescending, or escalatory. Not telling them hides the basis for the response. The sources reviewed here say little about this. Where the law does speak, it leans toward disclosure: people should be notified when a system can infer their emotions or intentions [6]. The practical compromise is to disclose the inference only when it changes what the assistant does, and then in the narrowest terms.

**Cultural and contextual variation.** Grice's framework assumes a shared goal and shared knowledge [1], and much human-AI interaction lacks both. Indirectness, politeness and high-context communication also mean that a "literal" reading is a stance rather than a neutral baseline. The sources reviewed here are almost entirely in English and were produced in North American and European institutions, and none tests whether the norms travel. That is a limit on the principle's generality, not a minor caveat.

**The measurement gap.** The largest limit is empirical. The principle is easy to state, hard to falsify, and currently unmeasured in the setting that matters. Until over-interpretation and its costs can be counted in real conversations, claims about its frequency or harm are hypotheses. The normative case can stand without that evidence. The empirical case cannot.

## References

[1]: https://plato.stanford.edu/entries/grice/ "Paul Grice, Stanford Encyclopedia of Philosophy"
[2]: http://collablab.northwestern.edu/CollabolabDistro/nucmc/ClarkAndBrennan-GroundingInCommunication-1991.pdf "Grounding in Communication, Clark and Brennan 1991"
[3]: https://model-spec.openai.com/ "OpenAI Model Spec"
[4]: https://www.anthropic.com/constitution "Claude's Constitution, Anthropic"
[5]: https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf "NIST AI 600-1, Generative AI Profile"
[6]: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689 "EU Artificial Intelligence Act, Regulation 2024/1689"
[7]: https://aclanthology.org/2020.emnlp-main.466/ "AmbigQA: Answering Ambiguous Open-domain Questions"
[8]: https://arxiv.org/abs/2605.25284 "Knowing but Not Showing: LLMs Recognize Ambiguity but Rarely Ask Clarifying Questions"
[9]: https://arxiv.org/abs/2310.13548 "Towards Understanding Sycophancy in Language Models"
[10]: https://proceedings.mlr.press/v229/ren23a.html "Robots That Ask For Help: Uncertainty Alignment for Large Language Model Planners"
[11]: https://pmc.ncbi.nlm.nih.gov/articles/PMC5958907/ "A Meta-Analysis of Motivational Interviewing Process"
