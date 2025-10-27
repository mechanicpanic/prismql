"""Generate synthetic customer support conversation data for PrismQL demo."""

import random
from typing import Any


def generate_demo_conversations() -> list[dict[str, Any]]:
    """
    Generate synthetic customer support conversations.

    Creates realistic patterns for demonstrating PrismQL:
    - Greetings
    - Problems and solutions
    - Questions and answers
    - Escalations
    - Thank you messages
    """
    conversations = []
    msg_id = 1

    # Conversation templates
    customers = ["alice", "bob", "charlie", "david", "emma", "frank"]
    agents = ["support_sarah", "support_mike", "support_lisa"]
    managers = ["manager_john", "manager_kate"]

    greetings = [
        "Hello, I need help",
        "Hi there!",
        "Hey, can someone assist me?",
        "Good morning",
        "Hi, I have a question",
    ]

    problems = [
        "My account is locked and I can't log in",
        "The payment failed but I was charged",
        "I'm getting an error message when uploading files",
        "The dashboard is not loading properly",
        "I can't access my data from yesterday",
        "The system is very slow today",
        "My export feature is broken",
        "I'm missing some important data",
    ]

    questions = [
        "What's the status of my request?",
        "When will this be fixed?",
        "How do I reset my password?",
        "Can you help me with this issue?",
        "Is this a known problem?",
        "How long will the maintenance take?",
    ]

    solutions = [
        "I've reset your account. Try logging in now.",
        "The issue has been fixed on our end.",
        "Please try clearing your cache and refreshing.",
        "I've processed the refund. You'll see it in 3-5 days.",
        "The system is back online now.",
        "I've escalated this to our technical team.",
    ]

    thanks = [
        "Thank you so much!",
        "Thanks for your help!",
        "Perfect, that worked!",
        "Appreciate your assistance",
        "Thanks, all set now",
    ]

    escalation_keywords = [
        "This is urgent",
        "I need to speak with a manager",
        "This is unacceptable",
        "I've been waiting too long",
        "Can I escalate this?",
    ]

    # Generate conversation 1: Simple problem resolution
    customer = random.choice(customers)
    agent = random.choice(agents)

    conversations.append(
        {"id": msg_id, "user": customer, "text": random.choice(greetings)}
    )
    msg_id += 1

    conversations.append(
        {"id": msg_id, "user": agent, "text": "Hi! How can I help you today?"}
    )
    msg_id += 1

    conversations.append(
        {"id": msg_id, "user": customer, "text": random.choice(problems)}
    )
    msg_id += 1

    conversations.append(
        {"id": msg_id, "user": agent, "text": "Let me check that for you..."}
    )
    msg_id += 1

    conversations.append(
        {"id": msg_id, "user": agent, "text": random.choice(solutions)}
    )
    msg_id += 1

    conversations.append(
        {"id": msg_id, "user": customer, "text": random.choice(thanks)}
    )
    msg_id += 1

    # Generate conversation 2: Question-answer pattern
    customer = random.choice(customers)
    agent = random.choice(agents)

    conversations.append(
        {"id": msg_id, "user": customer, "text": random.choice(questions)}
    )
    msg_id += 1

    conversations.append(
        {
            "id": msg_id,
            "user": agent,
            "text": "It should be resolved within the next hour.",
        }
    )
    msg_id += 1

    conversations.append(
        {"id": msg_id, "user": customer, "text": "Okay, I'll wait. Thanks!"}
    )
    msg_id += 1

    # Generate conversation 3: Escalation pattern
    customer = random.choice(customers)
    agent = random.choice(agents)
    manager = random.choice(managers)

    conversations.append(
        {"id": msg_id, "user": customer, "text": "I have a serious problem"}
    )
    msg_id += 1

    conversations.append(
        {"id": msg_id, "user": agent, "text": "I'm here to help. What's the issue?"}
    )
    msg_id += 1

    conversations.append(
        {
            "id": msg_id,
            "user": customer,
            "text": "The system deleted all my data. This is urgent!",
        }
    )
    msg_id += 1

    conversations.append(
        {
            "id": msg_id,
            "user": agent,
            "text": "I understand. Let me escalate this immediately.",
        }
    )
    msg_id += 1

    conversations.append(
        {
            "id": msg_id,
            "user": manager,
            "text": "I'm looking into this now. We'll recover your data.",
        }
    )
    msg_id += 1

    conversations.append(
        {"id": msg_id, "user": customer, "text": "Thank you for the quick response"}
    )
    msg_id += 1

    # Generate conversation 4: Multiple customers same problem
    problem = "The website is down"
    agent = random.choice(agents)

    for customer in random.sample(customers, 3):
        conversations.append({"id": msg_id, "user": customer, "text": f"Hi, {problem}"})
        msg_id += 1

    conversations.append(
        {
            "id": msg_id,
            "user": agent,
            "text": "We're aware of the issue and working on it.",
        }
    )
    msg_id += 1

    conversations.append(
        {"id": msg_id, "user": agent, "text": "The website is back online now!"}
    )
    msg_id += 1

    # Generate more varied conversations
    for _ in range(15):
        customer = random.choice(customers)
        agent = random.choice(agents)

        # Random conversation pattern
        pattern = random.choice(["simple", "complex", "question"])

        if pattern == "simple":
            conversations.append(
                {"id": msg_id, "user": customer, "text": random.choice(problems)}
            )
            msg_id += 1
            conversations.append(
                {"id": msg_id, "user": agent, "text": random.choice(solutions)}
            )
            msg_id += 1
            if random.random() > 0.5:
                conversations.append(
                    {"id": msg_id, "user": customer, "text": random.choice(thanks)}
                )
                msg_id += 1

        elif pattern == "complex":
            conversations.append(
                {"id": msg_id, "user": customer, "text": random.choice(greetings)}
            )
            msg_id += 1
            conversations.append(
                {"id": msg_id, "user": agent, "text": "Hi! How can I help?"}
            )
            msg_id += 1
            conversations.append(
                {"id": msg_id, "user": customer, "text": random.choice(problems)}
            )
            msg_id += 1
            conversations.append(
                {
                    "id": msg_id,
                    "user": customer,
                    "text": random.choice(escalation_keywords),
                }
            )
            msg_id += 1
            manager = random.choice(managers)
            conversations.append(
                {
                    "id": msg_id,
                    "user": manager,
                    "text": "I'm here to help. We'll resolve this.",
                }
            )
            msg_id += 1

        else:  # question
            conversations.append(
                {"id": msg_id, "user": customer, "text": random.choice(questions)}
            )
            msg_id += 1
            conversations.append(
                {"id": msg_id, "user": agent, "text": "Let me look into that..."}
            )
            msg_id += 1
            conversations.append(
                {"id": msg_id, "user": agent, "text": random.choice(solutions)}
            )
            msg_id += 1

    return conversations


def get_demo_dictionaries() -> dict[str, list[str]]:
    """Get user dictionaries for demo queries."""
    return {
        "greetings": ["hello", "hi", "hey", "good morning", "good afternoon"],
        "problems": [
            "error",
            "issue",
            "problem",
            "bug",
            "broken",
            "not working",
            "failed",
            "locked",
            "slow",
        ],
        "solutions": [
            "fixed",
            "resolved",
            "solved",
            "try",
            "reset",
            "cleared",
            "escalated",
        ],
        "thanks": ["thank", "thanks", "appreciate", "perfect", "great"],
        "urgent": ["urgent", "emergency", "asap", "immediately", "critical"],
        "questions": [
            "what",
            "when",
            "where",
            "how",
            "why",
            "can you",
            "status",
            "?",
        ],
    }


def generate_demo_custom_features(
    conversations: list[dict[str, Any]],
) -> dict[str, set[int]]:
    """
    Generate custom feature annotations for demo conversations.

    Simulates LLM/NLP annotations with features like sentiment, intent, priority.
    """
    custom_features: dict[str, set[int]] = {
        "sentiment_positive": set(),
        "sentiment_negative": set(),
        "sentiment_neutral": set(),
        "intent_greeting": set(),
        "intent_question": set(),
        "intent_complaint": set(),
        "intent_thanks": set(),
        "intent_response": set(),
        "priority_high": set(),
        "priority_normal": set(),
        "topic_technical": set(),
        "topic_account": set(),
        "topic_payment": set(),
    }

    for msg in conversations:
        text = msg["text"].lower()
        msg_id = msg["id"]

        # Sentiment analysis (rule-based simulation)
        positive_keywords = [
            "thank",
            "great",
            "perfect",
            "appreciate",
            "good",
            "back online",
            "fixed",
            "resolved",
        ]
        negative_keywords = [
            "problem",
            "issue",
            "error",
            "broken",
            "urgent",
            "unacceptable",
            "deleted",
            "failed",
        ]

        if any(kw in text for kw in positive_keywords):
            custom_features["sentiment_positive"].add(msg_id)
        elif any(kw in text for kw in negative_keywords):
            custom_features["sentiment_negative"].add(msg_id)
        else:
            custom_features["sentiment_neutral"].add(msg_id)

        # Intent classification
        if any(kw in text for kw in ["hi", "hello", "hey", "good morning"]):
            custom_features["intent_greeting"].add(msg_id)
        if any(kw in text for kw in ["what", "when", "where", "how", "why", "?"]):
            custom_features["intent_question"].add(msg_id)
        if any(
            kw in text
            for kw in ["problem", "issue", "unacceptable", "urgent", "broken"]
        ):
            custom_features["intent_complaint"].add(msg_id)
        if any(kw in text for kw in ["thank", "thanks", "appreciate"]):
            custom_features["intent_thanks"].add(msg_id)
        if msg["user"].startswith("support") or msg["user"].startswith("manager"):
            custom_features["intent_response"].add(msg_id)

        # Priority classification
        if any(
            kw in text for kw in ["urgent", "critical", "deleted", "serious", "asap"]
        ):
            custom_features["priority_high"].add(msg_id)
        else:
            custom_features["priority_normal"].add(msg_id)

        # Topic classification
        if any(kw in text for kw in ["error", "system", "loading", "slow", "website"]):
            custom_features["topic_technical"].add(msg_id)
        if any(kw in text for kw in ["account", "locked", "password", "login"]):
            custom_features["topic_account"].add(msg_id)
        if any(kw in text for kw in ["payment", "charged", "refund"]):
            custom_features["topic_payment"].add(msg_id)

    return custom_features


if __name__ == "__main__":
    # Generate and print sample data
    conversations = generate_demo_conversations()
    print(f"Generated {len(conversations)} messages")
    print("\nSample messages:")
    for msg in conversations[:10]:
        print(f"[{msg['id']}] {msg['user']}: {msg['text']}")

    # Generate custom features
    features = generate_demo_custom_features(conversations)
    print(f"\nGenerated {len(features)} custom features")
    for feature_name, msg_ids in sorted(features.items()):
        print(f"  {feature_name}: {len(msg_ids)} messages")
