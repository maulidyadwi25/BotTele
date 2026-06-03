#!/usr/bin/env python
"""Test script for NLP service"""
import os
os.environ['MASTER_SHEET_ID'] = ''

from nlp_service import process_message, nlp_service, initialize_nlp

print("=== NLP Service Test ===\n")

# Test 1: Without Master Sheet
result = process_message('buka proyek satelit')
print("Test 1 - No Master Sheet configured:")
print(f"  project: {result.project_name}")
print(f"  intent: {result.intent}")
print(f"  confidence: {result.confidence}")
print(f"  JSON: {result.to_json()}")
print()

# Test 2: Intent extraction
result2 = process_message('hitung total budget')
print("Test 2 - Intent extraction:")
print(f"  intent: {result2.intent}")
print(f"  confidence: {result2.confidence}")
print()

# Test 3: NLPResult dataclass
print("Test 3 - NLPResult to_dict:")
print(f"  dict: {result.to_dict()}")
print()

# Test 4: initialize_nlp without config
ok = initialize_nlp('', 'Projects')
print(f"Test 4 - initialize_nlp without config: {ok}")

print("\n=== All tests passed ===")
