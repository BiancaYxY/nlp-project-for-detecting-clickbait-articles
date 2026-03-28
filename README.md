# The Gossip Police

## Overview

The Gossip Police is an NLP-powered system designed to detect misleading or clickbait headlines in tabloid and lifestyle journalism.

It analyzes the relationship between an article’s headline and its actual content, helping users understand whether a title is genuinely supported or exaggerated for attention.

---

## Purpose

The main goal of this project is to combat misinformation and clickbait by automatically identifying discrepancies between sensational headlines and the real content of articles.

---

## Description

The system takes an article URL as input, extracts the headline and body text and applies multiple NLP techniques to evaluate their consistency.

It then produces a final verdict explained in a humorous and engaging tone by a virtual persona called "The Gossip Police", a witty media detective.

---

## Target Audience

- Online news readers  
- Users who want to avoid misleading or low-value articles  
- Anyone interested in filtering out media noise  

---

## Core Techniques

The pipeline combines several key NLP methods:

- Semantic Similarity  
  Measures whether the headline and article discuss the same topic

- Text Entailment (Natural Language Inference)  
  Determines whether the content supports the claim made in the headline

- Clickbait Detection  
  Classifies how sensationalized or misleading the headline is

- LLM-based Explanation  
  Generates a short clear and humorous explanation of the results using a detective persona

---

## Originality

The Gossip Police combines factual consistency analysis through entailment with stylistic detection through clickbait classification and explainability through LLM-generated narratives.

Instead of returning only scores the system provides an interpretable and engaging explanation that is both useful and memorable.

---

## How It Works

1. Input: Article URL  
2. Scraping: Extract headline and article text  
3. Preprocessing: Clean and normalize text  
4. NLP Analysis:
   - Semantic similarity  
   - Text entailment  
   - Clickbait detection  
5. Decision Engine: Generate verdict  
6. LLM Layer: Produce final explanation  

---
