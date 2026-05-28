"""LexaTrace — Patent Search Service (Simulated)

In production, this would query USPTO, EPO, and WIPO APIs.
For demo purposes, returns simulated patent matches.
"""

import random


SIMULATED_PATENTS = [
    {
        "patent_id": "US10,234,567",
        "title": "Method and System for Automated Image Processing Using Deep Learning",
        "office": "USPTO",
        "jurisdiction": "US",
        "filing_date": "2021-03-15",
        "abstract": "A method for processing digital images using a cascade of convolutional neural network layers with attention mechanisms to enhance image quality and extract semantic features.",
        "claims_excerpt": "Claim 1: A computer-implemented method comprising receiving an input image; applying convolutional filters at multiple scales; computing attention-weighted feature maps; generating an enhanced output image.",
        "inventors": "Smith, J.; Lee, K.; Patel, R.",
        "status": "Granted",
    },
    {
        "patent_id": "EP3,456,789",
        "title": "Natural Language Processing System for Document Classification",
        "office": "EPO",
        "jurisdiction": "EU",
        "filing_date": "2022-07-20",
        "abstract": "A system for classifying documents using transformer-based language models with fine-tuned classification heads for multi-label categorization across legal, technical, and scientific domains.",
        "claims_excerpt": "Claim 1: A document classification system comprising a tokenization module, a multi-layer transformer encoder, and a classification head with domain-specific output layers.",
        "inventors": "Mueller, A.; Garcia, M.",
        "status": "Published",
    },
    {
        "patent_id": "WO2023/012345",
        "title": "Machine Learning Pipeline for Automated Feature Engineering",
        "office": "WIPO",
        "jurisdiction": "Global",
        "filing_date": "2023-01-10",
        "abstract": "An automated machine learning pipeline that performs feature engineering using genetic programming, model selection through Bayesian optimization, and deployment in containerized environments.",
        "claims_excerpt": "Claim 1: A method for automated feature engineering comprising generating candidate features using genetic operators; evaluating fitness using cross-validated performance metrics.",
        "inventors": "Chen, W.; Nakamura, T.; Singh, P.",
        "status": "PCT Filed",
    },
    {
        "patent_id": "US11,789,012",
        "title": "Copyright Detection System Using Semantic Embeddings",
        "office": "USPTO",
        "jurisdiction": "US",
        "filing_date": "2022-11-05",
        "abstract": "A system for detecting potential copyright infringement by computing semantic embeddings of textual content and comparing them against a database of known copyrighted works using approximate nearest neighbor search.",
        "claims_excerpt": "Claim 1: A copyright detection method comprising encoding input text into vector embeddings; querying a vector index of copyrighted works; ranking matches by cosine similarity score.",
        "inventors": "Johnson, L.; Kim, S.",
        "status": "Granted",
    },
    {
        "patent_id": "EP4,567,890",
        "title": "Distributed Computing Framework for Large-Scale Data Analysis",
        "office": "EPO",
        "jurisdiction": "EU",
        "filing_date": "2023-04-18",
        "abstract": "A distributed computing framework that partitions large datasets across multiple processing nodes, applies map-reduce operations with fault tolerance, and aggregates results using consensus protocols.",
        "claims_excerpt": "Claim 1: A distributed data processing system comprising a coordinator node; multiple worker nodes; a fault-tolerant message bus; and a consensus-based result aggregator.",
        "inventors": "O'Brien, K.; Fernandez, A.",
        "status": "Under Examination",
    },
]


def search_patents(query_text: str, top_k: int = 5) -> list[dict]:
    """Simulate patent search across USPTO, EPO, and WIPO.

    In production, this would:
    1. Extract noun-phrase claims from the input using spaCy
    2. Query USPTO Open Data API, EPO OPS, and WIPO PATENTSCOPE
    3. Embed patent abstracts and compute similarity with input
    4. Rank and return top matches

    For the demo, returns simulated results with random scores.
    """
    results = []
    for patent in SIMULATED_PATENTS[:top_k]:
        # Simulate a relevance score (in production, computed via cosine similarity)
        score = round(random.uniform(0.55, 0.92), 4)
        results.append({
            **patent,
            "relevance_score": score,
            "risk_level": _classify_patent_risk(score),
        })

    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return results


def _classify_patent_risk(score: float) -> str:
    if score >= 0.85:
        return "high"
    elif score >= 0.70:
        return "medium"
    elif score >= 0.55:
        return "low"
    return "clear"
