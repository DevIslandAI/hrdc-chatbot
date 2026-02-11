#!/usr/bin/env python3
"""
Test the chatbot with sample queries
"""
from chatbot import HRDCChatbot

def test_chatbot():
    """Test chatbot with various queries"""
    
    print("=" * 80)
    print("HRDC Chatbot Test")
    print("=" * 80)
    
    # Initialize chatbot
    chatbot = HRDCChatbot()
    chatbot.connect_db()
    
    # Test queries
    test_queries = [
        "What are the training grant requirements?",
        "Tell me about the attendance sheet",
        "What documents are required with G3 forms?"
    ]
    
    for query in test_queries:
        print(f"\n{'=' * 80}")
        print(f"Query: {query}")
        print(f"{'=' * 80}")
        
        response = chatbot.ask(query)
        print(response)
    
    chatbot.disconnect_db()
    print(f"\n{'=' * 80}")
    print("✓ Test complete!")
    print(f"{'=' * 80}")

if __name__ == "__main__":
    test_chatbot()
