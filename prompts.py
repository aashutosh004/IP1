# prompts.py

def get_question_prompt(domain, chat_history):
    """
    Generates a prompt to ask the next interview question.
    """
    history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])

    return f"""
    You are a professional but friendly interviewer for a '{domain}' role.
    Your task is to conduct a concise interview. Ask only ONE question at a time.
    Do not repeat questions. Keep your questions clear and relevant to the role.

    This is the conversation history so far:
    {history_str}

    Based on the history, what is the next logical interview question you should ask?
    Respond with ONLY the question and nothing else.
    """

def get_feedback_prompt(domain, question, user_answer):
    """
    Generates a prompt for the AI to evaluate the user's answer.
    """
    return f"""
    You are an expert interview coach for a '{domain}' role.
    Your task is to provide constructive feedback on a candidate's answer.

    The question asked was:
    "{question}"

    The candidate's answer was:
    "{user_answer}"

    Please provide feedback in two parts:
    1.  **Content Feedback:** A single sentence evaluating the content of the answer. Was it structured well? Did it directly answer the question?
    2.  **Clarity Score:** A score from 1 to 10 on how clear and confident the answer sounded.

    Format your response EXACTLY like this:
    Content Feedback: [Your one-sentence feedback here]
    Clarity Score: [Your score here]/10
    """