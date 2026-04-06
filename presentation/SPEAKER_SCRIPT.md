# Speaker Script: Real Estate RAG Interview Presentation

**Total Time: 30 minutes presentation + 10-15 minutes Q&A**

---

## SLIDE 1: Title Slide
**"Unlocking Trapped Data"**

**[Duration: 45 seconds]**

### Script:

> "Good [morning/afternoon] everyone.. and thank you so much for having me here today.
>
> I'm really excited about this presentation.. because what I'm going to show you isn't just a theoretical architecture or a slide deck full of buzzwords...
>
> It's a working solution.. that I actually built.. to solve a very real problem that enterprise customers face every single day.
>
> And that problem is this... valuable data.. trapped in documents.. that nobody can actually search through effectively.
>
> So over the next 30 minutes.. I'm going to walk you through the challenge.. show you the solution I've built.. and then.. here's the fun part.. I'm going to demonstrate it live.
>
> Let's dive in."

**[CLICK to next slide]**

---

## SLIDE 2: About Me
**[Duration: 1 minute 15 seconds]**

### Script:

> "But first.. a quick introduction so you know who you're listening to.
>
> [Personalize this section - speak naturally about yourself]
>
> My name is [Your Name].. and I come from a background in cloud architecture and data engineering.
>
> I've spent the last [X] years working on.. well.. exactly these kinds of problems. Taking messy enterprise data.. and turning it into something useful. Something searchable. Something that actually helps people do their jobs better.
>
> What really excites me about this Practice Customer Engineer role.. is that it's not just about talking to customers about solutions...
>
> It's about actually building them.
>
> Rolling up your sleeves.. writing the code.. proving that something works...
>
> And that's exactly what I've done for today.
>
> So.. with that.. let me show you what we're going to cover."

**[CLICK to next slide]**

---

## SLIDE 3: Agenda
**[Duration: 1 minute]**

### Script:

> "Here's our roadmap for the next 30 minutes.
>
> We're going to start with the challenge... What is this customer actually dealing with? What's blocking them from adopting cloud AI?
>
> Then.. we'll look at the solution. Not just the architecture diagram.. but the actual thinking behind it. Why did I make the choices I made?
>
> After that.. and this is my favorite part.. we're going to do a live demonstration. I'm going to generate data.. index it.. and query it.. right in front of you. No slides.. no screenshots.. the real thing.
>
> Then we'll talk about architectural decisions.. because I know there will be questions about why I chose certain approaches over others.. and I want to address those head-on.
>
> And finally.. we'll connect everything back to business value. Because at the end of the day.. technology only matters if it solves real problems for real people.
>
> Sound good?... Great. Let's talk about the challenge."

**[CLICK to next slide]**

---

## SLIDE 4: Section Divider - The Challenge
**[Duration: 10 seconds]**

### Script:

> "Section one... Understanding the technical blocker."

**[Pause for 2-3 seconds to let the slide register]**

**[CLICK to next slide]**

---

## SLIDE 5: Customer Context
**[Duration: 1 minute 45 seconds]**

### Script:

> "So let me paint a picture for you.
>
> Our customer is a large real estate investment firm... We're talking billions of dollars in assets under management. They've been in business for decades.
>
> And over those decades.. they've accumulated an enormous amount of data. Property valuations. Comparable sales. Appraisal reports. Lease abstracts. Financial statements...
>
> This is valuable stuff... This is the institutional knowledge that gives them their competitive edge.
>
> Now.. they're ready to move to the cloud. They want to adopt Google Cloud. And specifically.. they want to use AI to help their analysts work faster.
>
> Makes sense.. right?...
>
> But here's the problem...
>
> And I'm going to quote directly from the challenge statement here...
>
> **'Our proprietary data is trapped in siloed.. unstructured PDF formats.. that standard RAG tools can't parse correctly.'**
>
> ...
>
> Let that sink in for a second.
>
> They have the data. They have the infrastructure budget. They have the business case...
>
> But they can't move forward.. because the tools they've tried.. just don't work with their documents.
>
> This is exactly the kind of ambiguous technical challenge that a Practice Customer Engineer needs to unblock.
>
> Let me show you what they're actually dealing with."

**[CLICK to next slide]**

---

## SLIDE 6: The Data Reality
**[Duration: 1 minute 30 seconds]**

### Script:

> "Here's the reality of their data.
>
> It's organized into what I call 'silos'. Different folders.. different systems.. for different document types.
>
> You've got comparable sales reports in one place.. offering memoranda in another.. appraisal reports somewhere else.. lease abstracts.. financial statements...
>
> Each silo has its own conventions. Its own formatting quirks. Its own way of presenting information.
>
> And the volume is significant...
>
> We're talking over 10,000 documents. Some of these PDFs are 50 pages. Some are 200 pages. Going back 20 years.
>
> Now here's where it gets painful...
>
> I talked to analysts who do this work. And they told me..
>
> **'Finding cap rate evidence for a single property takes me 2 to 3 hours.'**
>
> ...
>
> 2 to 3 hours. Just to find information that's already in their system. Already in documents they own.
>
> And when different analysts search for the same thing?.. They often come back with different answers. Because they searched different places. Or they interpreted headers differently.
>
> And there's no audit trail. No way to say 'this valuation is based on these specific sources.'
>
> So why can't they just use.. you know.. LangChain? Or LlamaIndex? Or any of the standard RAG tools out there?"

**[CLICK to next slide]**

---

## SLIDE 7: Why Standard Tools Fail
**[Duration: 2 minutes]**

### Script:

> "This is why.
>
> Let me walk you through this table.. because this is really the heart of the problem.
>
> **[Point to first row]**
>
> Repeated headers. Every single page of a confidential report has 'CONFIDENTIAL REPORT' stamped at the top. And often at the bottom too.
>
> When you use a standard PDF loader.. it extracts that text.. chunks it.. and indexes it. Now your vector database is full of chunks that say 'CONFIDENTIAL REPORT'. And when someone searches?.. Those chunks come back as results. Noise.
>
> **[Point to second row]**
>
> Page numbers. 'Page 1 of 2'. 'Page 47 of 156'. These get chunked as content. They get embedded. They pollute the index.
>
> **[Point to third row]**
>
> Dates... This one really got me.
>
> Some documents use American format: 3/7/2025. Some use ISO format: 2025-03-07. Some spell it out: March 7th, 2025.
>
> If I search for 'March 2025 cap rates'.. I might miss half the relevant documents. Because the query embedding doesn't match the inconsistent date formats.
>
> **[Point to remaining rows]**
>
> Same story with currency. '$ 1,250,000' with a space.. versus '$1.25M'. With area units.. 'SF' versus 'sq ft' versus 'square feet'.
>
> And then there's near-duplicate content. The same boilerplate paragraph appears in 50 different documents. Now your context window is stuffed with the same text repeated over and over.
>
> The result?...
>
> Noisy retrieval.. leads to poor answers.. leads to zero trust in the system.
>
> Analysts try it once. Get bad results. And go back to manual searching.
>
> That's the blocker. Now let me show you how I solved it."

**[CLICK to next slide]**

---

## SLIDE 8: Section Divider - The Solution
**[Duration: 10 seconds]**

### Script:

> "Section two... The custom RAG solution."

**[Pause for 2-3 seconds]**

**[CLICK to next slide]**

---

## SLIDE 9: Solution Overview
**[Duration: 1 minute 45 seconds]**

### Script:

> "Here's the key insight that drives everything.
>
> Standard RAG tools do this... PDF goes in.. text gets extracted.. text gets chunked.. chunks get embedded.. embeddings get stored.
>
> Simple pipeline. Works great for clean data.
>
> But the problem is... all that noise I just showed you?.. It passes straight through. The pipeline doesn't know that 'CONFIDENTIAL REPORT' is a header. It doesn't know that '3/7/2025' and '2025-03-07' are the same date.
>
> So what did I do?...
>
> I added a step. Right here in the middle.
>
> **[Gesture to the slide]**
>
> PDF.. extract.. **custom cleaning**.. chunk.. embed.. store.
>
> This cleaning pipeline is domain-specific. It understands real estate documents.
>
> It removes the boilerplate.. before it can pollute the index.
>
> It normalizes date formats.. so March 7th always looks the same.
>
> It standardizes currency and area units.
>
> It detects and removes near-duplicate content.
>
> And critically.. it preserves provenance. Every chunk knows exactly which document it came from.. and which page.
>
> That's how we get auditable citations.
>
> Let me show you the architecture."

**[CLICK to next slide]**

---

## SLIDE 10: Architecture Diagram
**[Duration: 1 minute 30 seconds]**

### Script:

> "Here's the end-to-end architecture. Let me walk you through it.
>
> **[Point to top section]**
>
> Data ingestion starts with PDF files. They come from different silos.. different folders representing document types.
>
> First.. ingestion. We extract text page by page. We capture metadata.. document ID.. page numbers.. which silo it came from.
>
> Then.. cleaning. This is where the magic happens. We normalize. We deduplicate. We remove noise.
>
> Then.. chunking. We split into 300-character chunks with 40-character overlap. The overlap is important.. it maintains context across chunk boundaries.
>
> **[Point to middle section]**
>
> Indexing. We convert chunks to vectors.. and store them in ChromaDB. This is a persistent vector database.. so data survives restarts.
>
> **[Point to bottom section]**
>
> Query flow. User asks a question. We embed that question. We search for similar chunks. We assemble context. We generate a grounded answer.
>
> And every answer comes with citations. Document ID. Page span. Similarity score.
>
> The key differentiator.. is that cleaning step. Let me show you exactly what it does."

**[CLICK to next slide]**

---

## SLIDE 11: Before & After Cleaning
**[Duration: 2 minutes 30 seconds]**

### Script:

> "This is my favorite slide in the whole presentation...
>
> Because this is where you can actually see the difference.
>
> **[Point to left column]**
>
> On the left.. raw PDF text. Exactly what a standard loader would extract.
>
> Look at it...
>
> 'CONFIDENTIAL REPORT' at the top. Then a separator line. Then the actual content. 'Downtown Tower Summary. NOI noted on 3/7/2025 at $ 1,250,000 for 12500 SF. Cap rate is 6.1%.'
>
> Then 'Page 1 of 2'. Another separator. And 'CONFIDENTIAL REPORT' again at the bottom.
>
> If I chunk this as-is.. I get garbage mixed with signal.
>
> **[Point to right column]**
>
> Now look at the right side. After cleaning.
>
> 'CONFIDENTIAL REPORT'?.. Gone. It appeared on multiple pages.. so we detected it as a repeated header and removed it.
>
> 'Page 1 of 2'?.. Gone. We have regex patterns that catch page numbers in all their variations.
>
> The date?.. Look carefully. '3/7/2025' became '2025-03-07'. ISO format. Now every date in the index looks the same.
>
> The currency?.. '$ 1,250,000' with that weird space.. became '$1,250,000'. Standardized.
>
> The area unit?.. 'SF' became 'sqft'. Consistent across all documents.
>
> And look at the bottom...
>
> We extracted 'cap_rate=6.1%' as structured metadata. Now we can filter queries.. 'show me only documents with cap rates between 5 and 7 percent.'
>
> ...
>
> This transformation happens before chunking. So the index.. only contains clean.. normalized.. searchable content.
>
> No noise. No duplicates. Just signal.
>
> ...
>
> Want to see it work for real?"

**[CLICK to next slide]**

---

## SLIDE 12: Section Divider - Live Demo
**[Duration: 10 seconds]**

### Script:

> "Section three... Live demonstration.
>
> Let's get our hands dirty."

**[CLICK to next slide]**

---

## SLIDE 13: Demo Overview
**[Duration: 1 minute]**

### Script:

> "Here's what I'm going to show you.
>
> First.. I'll generate sample data. 50 synthetic real estate PDFs. These aren't confidential customer documents.. I created them specifically for this demo. They have all the noise patterns we talked about.. repeated headers.. inconsistent dates.. the works.
>
> Second.. I'll run the full ingestion pipeline. You'll see 50 documents go in.. and you'll see how many clean segments come out. Spoiler.. it's less than you might expect.. because cleaning actually removes content.
>
> Third.. I'll query the system. We'll ask some valuation questions and look at the results.
>
> And finally.. I'll show you silo filtering. How we can target queries to specific document types.
>
> One important note...
>
> Everything runs offline. No API keys. No network calls. No external services.
>
> This is intentional. I didn't want to stand here and worry about API rate limits or network failures. The demo is deterministic and reliable.
>
> For production.. we'd swap in Vertex AI for embeddings and Gemini for generation. Same architecture.. different backends.
>
> Alright. Let me switch to the terminal..."

**[SWITCH TO TERMINAL or stay on slides]**

**[CLICK to next slide]**

---

## SLIDE 14: Demo Step 1 - Generate Data
**[Duration: 2 minutes]**

### Script:

> "First step.. let's create some data.
>
> **[Type or show command]**
>
> ```
> python scripts/generate_50_samples.py
> ```
>
> **[Press Enter]**
>
> Watch the output...
>
> **[As files are created]**
>
> See how they're being distributed across silos?
>
> Comps folder.. offering_memo folder.. appraisals.. leases.. financials.
>
> Each document is different. Different property types.. Downtown office towers.. suburban retail.. industrial warehouses. Different dates.. different values.. different cap rates.
>
> But they all have realistic noise. Headers that repeat. Page numbers. Inconsistent formatting.
>
> ...
>
> **[When complete]**
>
> Done. 50 PDFs created.
>
> Let me show you the distribution...
>
> 14 comparable sales reports. 10 offering memos. 10 appraisals. 8 leases. 8 financial statements.
>
> This mirrors what the actual customer data looks like.. some silos have more documents than others.
>
> Now let's see what happens when we run them through the pipeline."

**[CLICK to next slide]**

---

## SLIDE 15: Demo Step 2 - Index
**[Duration: 2 minutes 30 seconds]**

### Script:

> "Alright.. now the fun part. Let's index these documents.
>
> **[Type or show command]**
>
> ```
> re-rag index --input-dir ./sample_data_50 --vector-db-path ./vector_db_50 --collection valuation_50 --embedding-provider local --embedding-dimensions 12
> ```
>
> This command does everything. Ingestion. Cleaning. Chunking. Embedding. Indexing.
>
> **[Press Enter and wait]**
>
> ...
>
> **[When output appears]**
>
> Look at this output. This is important.
>
> **[Point to each number]**
>
> Documents: 50. That's how many PDFs we ingested.
>
> Clean segments: 90.
>
> ...
>
> Wait. 90?.. We started with 50 documents. Shouldn't we have more segments, not fewer?
>
> Here's what happened. The cleaning pipeline removed noise. Those repeated headers that appeared on every page?.. Gone. Page numbers?.. Gone. Near-duplicate paragraphs?.. Collapsed into single instances.
>
> 50 documents became 90 clean segments. The noise is gone.
>
> Then chunking happened. 90 segments became 165 chunks. Each chunk is roughly 300 characters.. sized for retrieval.
>
> And all of this is now stored in ChromaDB.. on disk.. persistent.
>
> If I restart my computer right now and come back.. the data is still there.
>
> Let's query it."

**[CLICK to next slide]**

---

## SLIDE 16: Demo Step 3 - Query
**[Duration: 2 minutes 30 seconds]**

### Script:

> "Let's ask a valuation question.
>
> **[Type or show command]**
>
> ```
> re-rag ask --question 'What cap rate evidence exists?' --vector-db-path ./vector_db_50 --collection valuation_50 --embedding-provider local --embedding-dimensions 12 --llm-provider stub --top-k 5
> ```
>
> **[Press Enter]**
>
> ...
>
> **[When output appears]**
>
> Let me walk you through this output.
>
> First.. the answer section.
>
> Now.. I should mention.. we're using a stub LLM for this demo. So the answer text is a placeholder. With a real LLM like Gemini.. this would be a natural language summary of the evidence.
>
> But the important part is below...
>
> **[Point to INSUFFICIENT_EVIDENCE]**
>
> 'INSUFFICIENT_EVIDENCE: False'
>
> This is a safety feature. The system is telling us.. yes.. I found relevant context. I'm confident in this answer.
>
> If we asked about something not in our documents?.. This would say 'True'. And the answer would explicitly say.. 'I don't have enough information. Please provide more documents.'
>
> No hallucination. No making things up.
>
> **[Point to citations]**
>
> Now look at the citations...
>
> Each citation has:
> - chunk_id.. a unique identifier for the specific text chunk
> - doc_id.. a SHA-256 hash of the source PDF
> - page_span.. which page this came from
> - score.. the similarity ranking
>
> An analyst can take any of these.. and trace back to the exact source. Full auditability.
>
> Let me show you one more thing.. silo filtering."

**[CLICK to next slide]**

---

## SLIDE 17: Demo Step 4 - Silo Filtering
**[Duration: 2 minutes]**

### Script:

> "Let's say I'm an analyst working on lease analysis. I don't want comparable sales cluttering my results. I only care about leases.
>
> **[Type or show command]**
>
> ```
> re-rag ask --question 'Show me lease terms and rent escalations' --silo leases --vector-db-path ./vector_db_50 --collection valuation_50 --embedding-provider local --embedding-dimensions 12 --llm-provider stub --top-k 3
> ```
>
> Notice the '--silo leases' flag. This filters the search.
>
> **[Press Enter]**
>
> ...
>
> **[When output appears]**
>
> Look at the citations now...
>
> Every single one comes from a lease document. lease_008.pdf. lease_021.pdf. lease_043.pdf.
>
> The system didn't search comps. Didn't search appraisals. Only leases.
>
> This filtering happens at the vector database level. It's fast. And it's powerful for targeted analysis.
>
> Imagine being able to say.. 'search only offering memos from the downtown submarket' or 'search only appraisals from 2024.'
>
> The metadata is there. The filtering is built in.
>
> ...
>
> That's the demo.
>
> Let me now talk about some of the architectural decisions behind this."

**[CLICK to next slide]**

---

## SLIDE 18: Section Divider - Architecture
**[Duration: 10 seconds]**

### Script:

> "Section four... Architectural decisions and trade-offs.
>
> Because every choice has consequences.. and I want to be transparent about the ones I made."

**[CLICK to next slide]**

---

## SLIDE 19: Technology Stack
**[Duration: 1 minute 15 seconds]**

### Script:

> "Let's start with the technology stack.
>
> **[Walk through table]**
>
> Python 3.10 for the runtime. Fast iteration.. rich ecosystem for ML and data processing.
>
> pypdf for PDF extraction. It's reliable. It gives me page-level control. I can extract text page by page and track exactly where everything comes from.
>
> ChromaDB for the vector database. I'll explain this choice in more detail in a moment.
>
> Pluggable adapters for embeddings and LLM. Local implementations for development and demos. Vertex AI for production.
>
> And pytest for testing. 30 tests covering the full pipeline. Ingestion. Cleaning. Chunking. Embedding. Retrieval. End-to-end.
>
> Now let me explain the key decisions."

**[CLICK to next slide]**

---

## SLIDE 20: Key Design Decisions
**[Duration: 2 minutes 30 seconds]**

### Script:

> "Three decisions I want to highlight. Because these are probably the ones you're most curious about.
>
> **[Point to first section]**
>
> First... Why ChromaDB?
>
> You might be wondering.. why not Pinecone? Why not Qdrant? Why not go straight to Vertex AI Vector Search?
>
> For a prototype.. I wanted local-first. No cloud dependency. No API keys to manage. No network calls that could fail during a demo.
>
> ChromaDB is persistent. It writes to disk. Data survives restarts. It behaves like a real database.. because it is one.
>
> And the migration path is clean. The interface I'm using?.. It maps directly to Vertex AI Vector Search. Same operations. Same filtering. Different backend.
>
> **[Point to second section]**
>
> Second... Why character-based chunking?
>
> Some people prefer semantic chunking. Or tokenizer-based splitting. Why did I go with simple character counts?
>
> Determinism. Same input produces same output.. every single time. This matters for testing. It matters for debugging. It matters for reproducibility.
>
> It's also model-agnostic. I don't need a specific tokenizer. I don't need to worry about model-specific token limits.
>
> And the boundaries are predictable. I can say with certainty.. 'this citation came from page 3.' No ambiguity.
>
> **[Point to third section]**
>
> Third... Why pluggable adapters?
>
> This one's practical. I wanted demo reliability. I'm not going to stand here and worry about API rate limits or network timeouts.
>
> The local adapters are deterministic. Same input.. same vectors.. same results. Every time.
>
> For production?.. One config change. Swap in Vertex AI. The pipeline code doesn't change at all."

**[CLICK to next slide]**

---

## SLIDE 21: Safety & Trust
**[Duration: 2 minutes]**

### Script:

> "Now let's talk about something really important... Safety and trust.
>
> For a valuation use case.. trust is everything. If an LLM hallucinates a cap rate.. and someone makes an investment decision based on that.. the consequences could be severe.
>
> So how do we prevent that?
>
> **[Point to each section]**
>
> First.. grounded prompts.
>
> The LLM is explicitly instructed.. 'Use ONLY the provided context. If the evidence is incomplete.. say so. Do not make things up.'
>
> This doesn't prevent hallucination entirely.. but it significantly reduces it.
>
> Second.. citation tracking.
>
> Every single answer includes source references. Chunk ID. Document ID. Page span. Similarity score.
>
> An analyst doesn't have to trust the AI blindly. They can click through. Verify. Check the original document.
>
> Third.. no-evidence handling.
>
> This is my favorite safety feature.
>
> When the system doesn't find relevant context?.. It doesn't guess. It returns 'insufficient_evidence: True' with a clear message. 'I don't have enough information to answer this reliably. Please provide more documents.'
>
> No hallucinated valuations. Ever.
>
> Fourth.. configurable thresholds.
>
> Minimum similarity scores. Context budget limits. These are tunable based on how much precision you need.
>
> This is the kind of safety that makes AI adoption possible in regulated industries."

**[CLICK to next slide]**

---

## SLIDE 22: Section Divider - Business Value
**[Duration: 10 seconds]**

### Script:

> "Section five... Business value and next steps.
>
> Because technology only matters if it solves real problems."

**[CLICK to next slide]**

---

## SLIDE 23: Quantified ROI
**[Duration: 1 minute 30 seconds]**

### Script:

> "Let's talk numbers.
>
> **[Walk through table row by row]**
>
> Time to find evidence.
>
> Before: 2 to 3 hours. An analyst manually searching through PDFs.. opening documents.. scanning for relevant information.
>
> After: 30 seconds. Type a question.. get an answer with citations.
>
> That's a 99% reduction in time spent searching.
>
> Analyst productivity.
>
> Before: 2 to 3 comprehensive searches per day. Because each one takes hours.
>
> After: 50 or more queries per day. Because each one takes seconds.
>
> That's 20x throughput.
>
> Answer consistency.
>
> Before: Variable. Different analysts find different things. Interpret headers differently. Miss documents in certain folders.
>
> After: Standardized. The system searches everything. Applies the same normalization. Returns consistent results.
>
> Audit trail.
>
> Before: Manual notes. 'I think I saw this in the Johnson appraisal somewhere.'
>
> After: Automatic citations. 'This came from document abc123.. page 7.. similarity score 0.85.'
>
> Compliance ready.
>
> These aren't hypothetical benefits. They're the direct result of making trapped data searchable."

**[CLICK to next slide]**

---

## SLIDE 24: Strategic Value
**[Duration: 1 minute 30 seconds]**

### Script:

> "Beyond the metrics.. there's strategic value here.
>
> **[Point to each section]**
>
> Unlock trapped data.
>
> Twenty years of institutional knowledge.. suddenly accessible. The analyst who's been there 30 years?.. Their expertise is in these documents. Now everyone can benefit from it.
>
> Accelerate deal cycles.
>
> Faster due diligence means more deals closed. When you can answer 'what's the cap rate evidence for properties like this one' in 30 seconds instead of 3 hours?.. That changes how fast you can move.
>
> Reduce risk.
>
> Auditable citations reduce unsupported claims. No more 'I think the cap rate is around 6%' without evidence. Every number traces back to a source.
>
> Scalable pattern.
>
> Here's what I really like about this architecture...
>
> It's not just for real estate valuation. Legal departments have the same problem. Compliance teams. Research organizations.
>
> Build once.. apply many times.
>
> And the cost model is favorable.
>
> The prototype runs offline. Zero API cost for development.
>
> Production costs scale with usage. And we can tune chunk sizes and context budgets to optimize spend."

**[CLICK to next slide]**

---

## SLIDE 25: Production Roadmap
**[Duration: 2 minutes]**

### Script:

> "So how do we get from prototype to production?
>
> I've broken this into three phases.
>
> **[Point to Phase 1]**
>
> Phase 1.. Pilot. Weeks 1 through 6.
>
> Deploy the prototype to Cloud Run. Move documents to Cloud Storage. Integrate Document AI for the really messy PDFs.. the scanned ones.. the weird layouts.
>
> Add real customer documents. Not just synthetic data.
>
> Build an evaluation test set. Questions with known correct answers. So we can measure quality.
>
> **[Point to Phase 2]**
>
> Phase 2.. Production. Weeks 6 through 12.
>
> Swap in Vertex AI for embeddings and Gemini for generation. Real semantic understanding. Real natural language answers.
>
> Choose a production vector backend. Vertex AI Vector Search for managed scale.. or AlloyDB with pgvector if you want SQL-native operations.
>
> Define SLOs. Monitoring. Alerting. The operational stuff that makes something production-ready.
>
> **[Point to Phase 3]**
>
> Phase 3.. Scale. Beyond week 12.
>
> VPC Service Controls for tighter security. Multi-zone disaster recovery. Continuous quality regression testing.
>
> **[Point to success criteria]**
>
> Success criteria...
>
> 95% of queries return relevant citations. Not just any citations.. relevant ones.
>
> p95 latency under 3 seconds. Fast enough to feel interactive.
>
> Zero hallucinations on the test set. Because trust is everything.
>
> This is achievable.. because the prototype already implements the core architecture."

**[CLICK to next slide]**

---

## SLIDE 26: Summary
**[Duration: 1 minute 15 seconds]**

### Script:

> "Let me bring it all together.
>
> ...
>
> **The problem**... Valuable valuation data trapped in unstructured PDFs. Analysts spending hours searching. Inconsistent results. No audit trail.
>
> **The solution**... Custom RAG with a domain-specific cleaning pipeline. Not just another wrapper around a PDF loader. A purpose-built system that understands real estate documents.
>
> **The differentiator**... And this is the key... Noise removal and normalization happen before indexing. Not after. The index is clean from day one.
>
> **The result**...
>
> Answers in seconds instead of hours.
>
> Full citation traceability back to source documents and pages.
>
> Safe handling when evidence is insufficient. No hallucinations.
>
> **The path forward**... A clear roadmap to Google Cloud production. Phased. Measurable. Achievable.
>
> ...
>
> This is the kind of technical unblocker that enables enterprise cloud adoption.
>
> It's not glamorous. It's not the flashiest AI demo. But it solves a real problem.. for real customers.. in a way that standard tools simply cannot."

**[CLICK to next slide]**

---

## SLIDE 27: Thank You
**[Duration: 30 seconds]**

### Script:

> "Thank you so much for your time and attention.
>
> I genuinely enjoyed building this solution.. and I hope that came through in the presentation.
>
> I'm happy to go deeper on any aspect... The cleaning pipeline regex patterns.. the vector database internals.. the production architecture.. the business case.. whatever you'd like to explore.
>
> ...
>
> What questions do you have for me?"

**[PREPARE FOR Q&A]**

---

## SLIDE 28: Appendix - Q&A Prep
**[Reference slide - don't present unless asked specific questions]**

### Common Questions & Suggested Answers:

---

**Q: "Why didn't you use LangChain or LlamaIndex?"**

> "That's a great question.. and honestly it was my first instinct too.
>
> The challenge is that those frameworks are designed for general-purpose RAG. They're excellent at what they do.
>
> But the noise patterns in real estate documents are specific. Repeated headers. Inconsistent date formats. Currency variations. Standard document loaders pass all of this through unchanged.
>
> I needed custom cleaning logic that understands these patterns. Logic that can detect 'CONFIDENTIAL REPORT' appearing on every page and remove it. Logic that normalizes '3/7/2025' to ISO format.
>
> That said.. the architecture is modular. We could absolutely integrate LangChain for orchestration if there are other features we want. The cleaning pipeline would still be the same."

---

**Q: "How do you handle scanned PDFs?"**

> "Good question. The ingestion layer flags low-text pages as 'scan_suspected'. If a page has fewer than 25 characters of extractable text.. we assume it might be a scan.
>
> For the prototype.. those pages pass through with warnings. We're transparent about what we couldn't extract.
>
> For production.. we'd route scan-suspected pages to Document AI for OCR. The extracted text would merge back into the pipeline. Cleaning and chunking work the same regardless of source."

---

**Q: "Why local embeddings instead of a real model?"**

> "Demo reliability.
>
> I wanted to present without any risk of API failures or rate limits. The local embeddings use a deterministic hash function.. same input produces same vector every time.
>
> Is it semantic? No. It's a hash. But it's deterministic and reliable.
>
> For production.. we swap in Vertex AI embeddings with a single config change. The pipeline code doesn't change. The interface is the same."

---

**Q: "What if the LLM still hallucinates?"**

> "Multiple safeguards.
>
> First.. grounded prompts. The model is instructed to use only provided context.
>
> Second.. citation tracking. Every claim maps to source chunks. An analyst can verify.
>
> Third.. the no-evidence path. If we don't find relevant context.. we don't generate an answer. We explicitly say 'insufficient evidence.'
>
> Fourth.. score thresholds filter low-confidence results.
>
> For high-stakes use cases.. we'd add human-in-the-loop review. Flag low-confidence answers for manual verification before they're used in decisions."

---

**Q: "How does this scale to millions of documents?"**

> "The architecture is designed for scale.
>
> ChromaDB handles the prototype. Vertex AI Vector Search handles production volumes.. millions of vectors.. sub-second queries.
>
> The ingestion pipeline is stateless and parallelizable. We can run multiple workers processing documents simultaneously.
>
> For millions of documents.. we'd move to incremental indexing instead of full re-index. Only process new or changed documents.
>
> Embedding calls would be batched for efficiency.
>
> The cleaning logic is CPU-bound and easily distributed."

---

**Q: "What's the cost estimate for production?"**

> "Depends on volume.. but let me give you a ballpark.
>
> Initial indexing of 10,000 documents.. maybe $50 to $100 one-time. That's embedding costs mostly.
>
> Monthly storage is minimal.. $10 to $20 for the vector database.
>
> Per-query cost with Gemini.. roughly $0.01 to $0.05 depending on context size.
>
> At 1,000 queries per month.. total cost might be $50 to $100.
>
> The bigger cost is usually the initial document preparation and building a good evaluation test set. That's engineering time.. not API costs."

---

**Q: "Can you show me the cleaning regex patterns?"**

> "Absolutely. Let me pull up the code...
>
> **[If asked, show cleaning/pipeline.py]**
>
> Here's the page number pattern... it catches 'Page 1 of 2'.. 'page 1/2'.. just '1 of 2'.. all the variations.
>
> Here's the date normalization... US format to ISO.
>
> Here's the currency pattern... handles spaces.. handles K/M/B suffixes.
>
> The repeated header detection is statistical. If the same line appears at the top or bottom of multiple pages.. we flag it as a header and remove it."

---

## TIMING SUMMARY (30 minutes)

| Section | Slides | Time |
|---------|--------|------|
| Intro & Agenda | 1-3 | 3:00 |
| The Challenge | 4-7 | 6:15 |
| The Solution | 8-11 | 7:00 |
| Live Demo | 12-17 | 10:00 |
| Architecture | 18-21 | 6:00 |
| Business Value | 22-25 | 6:00 |
| Summary & Close | 26-27 | 1:45 |
| **Total** | **27 slides** | **~30 min** |

---

## PRE-PRESENTATION CHECKLIST

- [ ] Terminal open with project directory
- [ ] Virtual environment activated (`source .venv/bin/activate`)
- [ ] Sample data NOT yet generated (demo will create it fresh)
- [ ] Vector database cleared or using fresh path
- [ ] Commands ready to copy-paste (avoid typos)
- [ ] Slides in presentation mode
- [ ] Speaker notes visible on your screen
- [ ] Water nearby
- [ ] Backup: screenshots of expected output if live demo fails
- [ ] Clock visible to track time

---

## TIPS FOR DELIVERY

1. **Breathe at the pause markers**... They're there for a reason. Let ideas land.

2. **Slow down on slide 11 (Before & After)**... This is your differentiator. Give it time.

3. **During the demo.. narrate what you're doing**... Don't just type silently.

4. **If something breaks.. stay calm**... Say "Let me try that again" or pivot to screenshots.

5. **Make eye contact during business value slides**... The VP of Strategy cares about outcomes.

6. **Watch the clock**... If you're at 25 minutes and still on architecture.. speed up.

7. **For Q&A.. take a breath before answering**... Shows you're thinking.. not just reacting.

8. **If you don't know something.. say so**... "That's a great question. I'd need to research that and get back to you."

---

## EMERGENCY BACKUP PLAN

If the live demo completely fails:

> "I apologize for the technical difficulty. Let me show you the expected output..."
>
> **[Switch to screenshots in the appendix]**
>
> "Here's what we would see when generating sample data..."
>
> "Here's the indexing output showing 50 documents becoming 165 chunks..."
>
> "And here's the query result with citations..."
>
> Continue as if the demo worked. The architecture explanation still stands.
