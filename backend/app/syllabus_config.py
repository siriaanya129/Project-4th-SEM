# EL_Sem4/backend/app/syllabus_config.py

# This file defines the structure of the syllabus.
# The 'unit_name' fields MUST match the 'unit_name' used in your 'question_templates.json'.
# The 'sub_topics' list under each main topic should ideally align with 'subtopic_name' in question_templates.json.

SYLLABUS_TOPICS = {
    # --- UNIT I: Descriptive Statistics ---
    "Describing data sets - Frequency tables and graphs, relative frequency tables and graphs": {
        "unit_name": "Unit-I Descriptive Statistics", "parent": None, "bloom": "Understand", "difficulty_rating": 2,
        "sub_topics": ["Frequency tables", "Relative frequency tables", "Graphical representation of frequency", "Cumulative frequency"]
    },
    "Describing data sets - Grouped data, histograms": {
        "unit_name": "Unit-I Descriptive Statistics", "parent": "Describing data sets - Frequency tables and graphs, relative frequency tables and graphs", "bloom": "Apply", "difficulty_rating": 3,
        "sub_topics": ["Grouped data construction", "Histograms construction", "Interpreting histograms (shape, center, spread)"]
    },
    "Describing data sets - Summarising data sets - Sample Mean, sample median, sample mode": {
        "unit_name": "Unit-I Descriptive Statistics", "parent": "Describing data sets - Grouped data, histograms", "bloom": "Understand", "difficulty_rating": 3,
        "sub_topics": ["Sample Mean calculation", "Sample Median calculation", "Sample Mode identification", "Choosing appropriate measure of central tendency", "Properties of mean, median, mode"]
    },
    "Describing data sets - sample variance and sample standard deviation": {
        "unit_name": "Unit-I Descriptive Statistics", "parent": "Describing data sets - Summarising data sets - Sample Mean, sample median, sample mode", "bloom": "Apply", "difficulty_rating": 4,
        "sub_topics": ["Sample Variance calculation (n-1 denominator)", "Sample Standard Deviation calculation", "Interpretation of variance/std dev as measures of spread", "Range"]
    },
    "Describing data sets - percentiles and box-plots": {
        "unit_name": "Unit-I Descriptive Statistics", "parent": "Describing data sets - sample variance and sample standard deviation", "bloom": "Analyze", "difficulty_rating": 5,
        "sub_topics": ["Percentiles calculation (Quartiles, Deciles)", "Interquartile Range (IQR)", "Box-plot construction", "Interpreting box-plots (skewness, outliers, spread)"]
    },

    # --- UNIT II: Sampling and Distributions ---
    "Types of sampling": {
        "unit_name": "Unit-II Sampling and Distributions", "parent": None, "bloom": "Remember", "difficulty_rating": 3,
        "sub_topics": ["Simple Random Sampling", "Stratified Sampling", "Cluster Sampling", "Systematic Sampling", "Convenience Sampling", "Judgment Sampling"]
    },
    "Sample Mean (Sampling Distribution Context)": {
        "unit_name": "Unit-II Sampling and Distributions", "parent": "Types of sampling", "bloom": "Understand", "difficulty_rating": 4,
        "sub_topics": ["Concept of sample mean as a random variable", "Expected value of sample mean E(x̄)", "Standard Error of the Mean (SEM)"]
    },
    "Sample Variance (Sampling Distribution Context)": {
        "unit_name": "Unit-II Sampling and Distributions", "parent": "Sample Mean (Sampling Distribution Context)", "bloom": "Understand", "difficulty_rating": 4,
        "sub_topics": ["Concept of sample variance as a random variable", "Unbiased estimator property (n-1)"]
    },
    "Sampling distributions from a normal population": {
        "unit_name": "Unit-II Sampling and Distributions", "parent": "Sample Variance (Sampling Distribution Context)", "bloom": "Apply", "difficulty_rating": 6,
        "sub_topics": ["Distribution of sample mean when population is normal", "Properties of this sampling distribution"]
    },
     "Sampling from a finite population": {
        "unit_name": "Unit-II Sampling and Distributions", "parent": "Types of sampling", "bloom": "Apply", "difficulty_rating": 5,
        "sub_topics": ["Finite Population Correction (FPC) factor application and interpretation"]
    },
    "Normal Distribution (Properties and Applications)": { # Broadened
        "unit_name": "Unit-II Sampling and Distributions", "parent": "Describing data sets - Grouped data, histograms", # Linked to visual understanding
        "bloom": "Understand", "difficulty_rating": 5,
        "sub_topics": ["Properties of Normal Distribution (bell shape, symmetry)", "Standard Normal Distribution (Z-scores calculation and interpretation)", "Empirical Rule (68-95-99.7)", "Using Z-tables or calculators for probabilities"]
    },
    "Binomial Distribution": { # Separated for clarity
        "unit_name": "Unit-II Sampling and Distributions", "parent": None, "bloom": "Apply", "difficulty_rating": 6,
        "sub_topics": ["Bernoulli trials", "Binomial probability formula P(X=k)", "Mean (np) and Variance (np(1-p)) of Binomial", "Shape of Binomial distribution"]
    },
    "Poisson Distribution": { # Separated for clarity
        "unit_name": "Unit-II Sampling and Distributions", "parent": None, "bloom": "Apply", "difficulty_rating": 6,
        "sub_topics": ["Conditions for Poisson process", "Poisson probability formula P(X=k)", "Mean (λ) and Variance (λ) of Poisson", "Applications for rare events"]
    },
    "Approximating binomial, Poisson distributions using normal distribution": {
        "unit_name": "Unit-II Sampling and Distributions", "parent": "Normal Distribution (Properties and Applications)", "bloom": "Apply", "difficulty_rating": 7,
        "sub_topics": ["Normal approximation to Binomial (conditions, continuity correction)", "Normal approximation to Poisson (conditions, continuity correction)"]
    },

    # --- UNIT III: Correlation, Covariance and Independent Random Variables ---
    "Joint behavior of random variables": {
        "unit_name": "Unit-III Correlation, Covariance and Independent Random Variables", "parent": None, "bloom": "Understand", "difficulty_rating": 5,
        "sub_topics": ["Joint probability distributions (conceptual for discrete variables)", "Marginal probability distributions (conceptual)", "Conditional probability distributions (conceptual)"]
    },
    "Correlation": {
        "unit_name": "Unit-III Correlation, Covariance and Independent Random Variables", "parent": "Joint behavior of random variables", "bloom": "Apply", "difficulty_rating": 6,
        "sub_topics": ["Pearson correlation coefficient (calculation from data/summary stats)", "Interpretation of correlation (strength, direction)", "Properties of r (-1 to 1)", "Correlation vs. Causation"]
    },
    "Covariance": {
        "unit_name": "Unit-III Correlation, Covariance and Independent Random Variables", "parent": "Joint behavior of random variables", "bloom": "Apply", "difficulty_rating": 6,
        "sub_topics": ["Covariance calculation (from data/summary stats)", "Interpretation of covariance sign", "Relationship between covariance and correlation", "Cov(X,Y) for independent variables"]
    },
    "Variance-covariance matrix": {
        "unit_name": "Unit-III Correlation, Covariance and Independent Random Variables", "parent": "Covariance", "bloom": "Analyze", "difficulty_rating": 8,
        "sub_topics": ["Structure for two or more variables", "Properties (symmetry, positive semi-definite)", "Diagonal (variances) and off-diagonal (covariances) elements"]
    },
    "Independent random variables": {
        "unit_name": "Unit-III Correlation, Covariance and Independent Random Variables", "parent": "Joint behavior of random variables", "bloom": "Apply", "difficulty_rating": 7,
        "sub_topics": ["Definition of statistical independence", "E(XY) = E(X)E(Y) for independent variables", "Independence implies uncorrelation (but not vice-versa)"]
    },
    "Sums of independent random variables": {
        "unit_name": "Unit-III Correlation, Covariance and Independent Random Variables", "parent": "Independent random variables", "bloom": "Analyze", "difficulty_rating": 8,
        "sub_topics": ["Mean of a sum/difference: E(X±Y) = E(X)±E(Y)", "Variance of a sum/difference of independent variables: Var(X±Y) = Var(X)+Var(Y)", "Variance of a linear combination: Var(aX+bY)"]
    },
    "Law of Large Numbers (LLN)": { # Explicitly named
        "unit_name": "Unit-III Correlation, Covariance and Independent Random Variables", "parent": "Sample Mean (Sampling Distribution Context)", "bloom": "Analyze", "difficulty_rating": 8,
        "sub_topics": ["Statement and interpretation (sample mean converges to population mean)", "Distinction from CLT"]
    },
    "Central Limit Theorem (CLT)": { # Explicitly named
        "unit_name": "Unit-III Correlation, Covariance and Independent Random Variables", "parent": "Sampling distributions from a normal population", "bloom": "Analyze", "difficulty_rating": 8,
        "sub_topics": ["Statement and conditions for applicability (large n)", "Implications for the sampling distribution of the sample mean"]
    },

    # --- UNIT IV: Large Sample Estimation ---
    "Statistical Inference (Estimation)": {
        "unit_name": "Unit-IV Large Sample Estimation", "parent": "Central Limit Theorem (CLT)", "bloom": "Understand", "difficulty_rating": 6,
        "sub_topics": ["Objective of estimation", "Point estimation vs. Interval estimation"]
    },
    "Types of Estimators (Properties)": { # Renamed
        "unit_name": "Unit-IV Large Sample Estimation", "parent": "Statistical Inference (Estimation)", "bloom": "Remember", "difficulty_rating": 5,
        "sub_topics": ["Unbiasedness", "Consistency", "Efficiency (relative)", "Sufficiency (conceptual)"]
    },
    "Point estimation of a population parameter": { # Kept specific
        "unit_name": "Unit-IV Large Sample Estimation", "parent": "Types of Estimators (Properties)", "bloom": "Apply", "difficulty_rating": 7,
        "sub_topics": ["Point estimator for population mean (μ)", "Point estimator for population proportion (p)", "Point estimator for population variance (σ²)"]
    },
    "Interval Estimation - Constructing a confidence interval": { # Kept specific
        "unit_name": "Unit-IV Large Sample Estimation", "parent": "Point estimation of a population parameter", "bloom": "Apply", "difficulty_rating": 7,
        "sub_topics": ["Concept of a confidence interval", "Margin of error"]
    },
    "Large-Sample Confidence Interval for a Population Mean": {
        "unit_name": "Unit-IV Large Sample Estimation", "parent": "Interval Estimation - Constructing a confidence interval", "bloom": "Apply", "difficulty_rating": 8,
        "sub_topics": ["Formula using z-distribution (σ known or large n with s)", "Formula using t-distribution (σ unknown, if applicable or mentioned)"]
    },
    "Interpreting the confidence interval": {
        "unit_name": "Unit-IV Large Sample Estimation", "parent": "Large-Sample Confidence Interval for a Population Mean", "bloom": "Analyze", "difficulty_rating": 7,
        "sub_topics": ["Meaning of the confidence level (e.g., 95%)", "Correct vs. incorrect interpretations", "Factors affecting width of CI"]
    },
    "Large sample confidence interval for a population proportion": {
        "unit_name": "Unit-IV Large Sample Estimation", "parent": "Interpreting the confidence interval", "bloom": "Apply", "difficulty_rating": 8,
        "sub_topics": ["Formula using z-distribution", "Conditions for validity (np > 5, n(1-p) > 5)"]
    },
    "Estimating the difference between two population means": {
        "unit_name": "Unit-IV Large Sample Estimation", "parent": "Large sample confidence interval for a population proportion", "bloom": "Analyze", "difficulty_rating": 8,
        "sub_topics": ["CI for (μ1 - μ2) with independent samples (known/unknown variances, large samples)", "Interpreting the CI for difference (e.g., if it contains zero)"]
    },
    "Estimating the difference between two binomial distributions (proportions)": {
        "unit_name": "Unit-IV Large Sample Estimation", "parent": "Estimating the difference between two population means", "bloom": "Analyze", "difficulty_rating": 8,
        "sub_topics": ["CI for (p1 - p2) with independent samples", "Interpreting the CI for difference"]
    },
    "One-sided confidence bounds": {
        "unit_name": "Unit-IV Large Sample Estimation", "parent": "Estimating the difference between two binomial distributions (proportions)", "bloom": "Apply", "difficulty_rating": 7,
        "sub_topics": ["Concept of upper/lower confidence bounds", "Calculation for mean/proportion"]
    },
    "Choosing the Sample size (for Estimation)": {
        "unit_name": "Unit-IV Large Sample Estimation", "parent": "One-sided confidence bounds", "bloom": "Apply", "difficulty_rating": 7,
        "sub_topics": ["Sample size for estimating population mean (given desired margin of error and confidence)", "Sample size for estimating population proportion (given desired margin of error and confidence, with/without prior p)"]
    },

    # --- UNIT V: Hypothesis Testing ---
    "Testing of hypothesis about population parameters": { # Combined
        "unit_name": "Unit-V Hypothesis Testing", "parent": "Statistical Inference (Estimation)", "bloom": "Understand", "difficulty_rating": 6,
        "sub_topics": ["Formulating Null (H₀) and Alternative (H₁) hypotheses", "One-tailed vs. Two-tailed tests"]
    },
    "Statistical Test of hypothesis": { # Separated as per syllabus list
        "unit_name": "Unit-V Hypothesis Testing", "parent": "Testing of hypothesis about population parameters", "bloom": "Understand", "difficulty_rating": 6,
        "sub_topics": ["Test statistic concept", "Critical value(s) and Rejection region", "Decision rule"]
    },
    "A large-sample test about the population mean": {
        "unit_name": "Unit-V Hypothesis Testing", "parent": "Statistical Test of hypothesis", "bloom": "Apply", "difficulty_rating": 7,
        "sub_topics": ["Z-test for population mean (σ known or large n with s)", "T-test for population mean (σ unknown, if discussed for large samples or as a general case)"]
    },
    "Essentials of the test, calculating the p-value": { # Split for granularity
        "unit_name": "Unit-V Hypothesis Testing", "parent": "A large-sample test about the population mean", "bloom": "Analyze", "difficulty_rating": 8,
        "sub_topics": ["Calculating p-value for z-tests and t-tests", "Interpreting p-value in relation to significance level (α)"]
    },
    "Two types of errors, power of a statistical test": { # Split for granularity
        "unit_name": "Unit-V Hypothesis Testing", "parent": "Essentials of the test, calculating the p-value", "bloom": "Analyze", "difficulty_rating": 8,
        "sub_topics": ["Type I error (α) definition and consequences", "Type II error (β) definition and consequences", "Power of a test (1-β) definition and factors affecting it"]
    },
    "A large-sample test of hypothesis for the difference between two population means": {
        "unit_name": "Unit-V Hypothesis Testing", "parent": "Two types of errors, power of a statistical test", "bloom": "Apply", "difficulty_rating": 8,
        "sub_topics": ["Two-sample z-test for difference in means (independent samples)", "Two-sample t-test for difference in means (independent samples, equal/unequal variances if covered)"]
    },
    "Hypothesis testing and confidence intervals": { # Relationship focused
        "unit_name": "Unit-V Hypothesis Testing", "parent": "A large-sample test of hypothesis for the difference between two population means", "bloom": "Analyze", "difficulty_rating": 8,
        "sub_topics": ["Duality: Using a CI to perform a two-tailed hypothesis test (and vice-versa)"]
    },
    "Hypothesis testing for the binomial (proportion)": { # For a single proportion
        "unit_name": "Unit-V Hypothesis Testing", "parent": "Hypothesis testing and confidence intervals", "bloom": "Apply", "difficulty_rating": 7,
        "sub_topics": ["One-sample z-test for population proportion", "Conditions for validity"]
    },
    "Some comments on testing of hypothesis": {
        "unit_name": "Unit-V Hypothesis Testing", "parent": "Hypothesis testing for the binomial (proportion)", "bloom": "Evaluate", "difficulty_rating": 7,
        "sub_topics": ["Statistical significance vs. Practical importance", "Assumptions underlying various hypothesis tests", "Limitations of hypothesis testing"]
    }
}

# QUESTION_TOPIC_MAP:
# This maps (difficulty_level, difficulty_type) to a list of broad topic names.
# With detailed tagging in question_templates.json, this map is more for high-level analysis.
# Ensure topic names here are keys from SYLLABUS_TOPICS.
QUESTION_TOPIC_MAP = {
    ("easy", "direct"): [
        "Describing data sets - Frequency tables and graphs, relative frequency tables and graphs",
        "Describing data sets - Summarising data sets - Sample Mean, sample median, sample mode",
        "Types of sampling", "Statistical Inference (Estimation)",
        "Testing of hypothesis about population parameters", "Statistical Test of hypothesis",
        "Sample Mean (Sampling Distribution Context)", "Normal Distribution (Properties and Applications)"
    ],
    ("medium", "direct"): [
        "Describing data sets - Grouped data, histograms",
        "Sample Variance (Sampling Distribution Context)",
        "Point estimation of a population parameter",
        "A large-sample test about the population mean",
        "Essentials of the test, calculating the p-value",
        "Binomial Distribution", "Poisson Distribution"
    ],
    ("hard", "direct"): [
        "Constructing a confidence interval, Large-Sample Confidence Interval for a Population Mean",
        "A large-sample test of hypothesis for the difference between two population means",
        "Hypothesis testing for the binomial (proportion)",
        "Sums of independent random variables"
    ],
    ("easy", "logical reasoning"): [
        "Describing data sets - percentiles and box-plots",
        "Independent random variables"
    ],
    ("medium", "logical reasoning"): [
        "Sampling distributions from a normal population",
        "Correlation", "Covariance",
        "Interpreting the confidence interval",
        "Two types of errors, power of a statistical test",
        "Some comments on testing of hypothesis"
    ],
    ("hard", "logical reasoning"): [
        "Variance-covariance matrix", "Law of Large Numbers (LLN)", "Central Limit Theorem (CLT)",
        "Estimating the difference between two binomial distributions (proportions)", # Interpretation aspects
        "Hypothesis testing and confidence intervals"
    ],
    ("easy", "aptitude"): [
        "Describing data sets - sample variance and sample standard deviation" # e.g. range
    ],
    ("medium", "aptitude"): [
        "Interval Estimation - Constructing a confidence interval",
        "Approximating binomial, Poisson distributions using normal distribution",
        "Choosing the Sample size (for Estimation)",
        "One-sided confidence bounds"
    ],
    ("hard", "aptitude"): [
        "Large sample confidence interval for a population proportion",
        "Estimating the difference between two population means", # Calculation
        "Estimating the difference between two binomial distributions (proportions)" # Calculation
    ]
}

def get_topics_for_unit(unit_full_name: str) -> list:
    """Returns a list of main topic names for a given unit_full_name."""
    return [topic for topic, details in SYLLABUS_TOPICS.items() if details.get("unit_name") == unit_full_name]

def get_unit_names() -> list:
    """Returns a list of unique unit names from the syllabus."""
    unit_names = set()
    for topic_details in SYLLABUS_TOPICS.values():
        unit_names.add(topic_details["unit_name"])
    return sorted(list(unit_names))