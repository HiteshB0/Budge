import os
from typing import Dict
import json
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

class QuestionGenerator:
    """Generates Socratic questions that provoke reflection, NOT advice"""
    
    FORBIDDEN_PATTERNS = [
        "you should",
        "try to",
        "consider",
        "it would be better",
        "I recommend",
        "why don't you"
    ]
    
    def generate_question(
        self, 
        pattern_code: str,
        bias_name: str,
        pattern_details: Dict,
        concept_context: Dict
    ) -> str:
        """Generate ONE good reflection question"""
        
        prompt = f"""You are a financial education coach using the Socratic method.

DETECTED PATTERN:
Type: {pattern_code}
Cognitive Bias: {bias_name}
User's Data: {json.dumps(pattern_details)}

CONCEPT CONTEXT:
{concept_context['definition']}

YOUR TASK: Generate ONE powerful reflection question that:
1. Uses their specific numbers/merchants from pattern_details
2. Makes them THINK about their decision-making process
3. Has no obvious "right" answer
4. Is NOT advice in disguise

FORBIDDEN PHRASES (never use these):
- "Have you considered..."
- "Why don't you..."
- "You should think about..."
- "Would it be better if..."

GOOD QUESTION TYPES:
- Consequence exploration: "If you kept this pattern for 2 years, what would change?"
- Value clarification: "What does spending $X on Y say about your priorities right now?"
- Emotional awareness: "What feeling are you trying to create with these purchases?"
- Future self: "Would your future self thank you for this, or wish you'd chosen differently?"

Generate ONE question (return ONLY the question, no preamble):"""
        
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 150
                },
                timeout=30
            )
            
            if response.status_code == 200:
                question = response.json()["choices"][0]["message"]["content"].strip().strip('"')
                
                for forbidden in self.FORBIDDEN_PATTERNS:
                    if forbidden in question.lower():
                        return self._template_fallback(pattern_code, pattern_details)
                
                return question
            else:
                return self._template_fallback(pattern_code, pattern_details)
                
        except Exception as e:
            print(f"Groq API error: {e}")
            return self._template_fallback(pattern_code, pattern_details)
    
    def _template_fallback(self, pattern_code: str, details: Dict) -> str:
        """Deterministic fallback if LLM gives advice"""
        templates = {
            "LATTE_FACTOR": f"You've spent ${details.get('avg_amount', 0) * details.get('count', 0):.0f} on small {details.get('merchant', 'purchases')} recently. What would that money unlock if you redirected it for 6 months?",
            "IMPULSE_CLUSTER": f"On {details.get('date', 'that day')}, you made {details.get('count', 'multiple')} purchases totaling ${details.get('total_spent', 0):.0f}. What was happening in your life that day?",
            "SUBSCRIPTION_CREEP": f"You have {details.get('count', 'several')} subscriptions costing ${details.get('monthly_total', 0):.0f}/month. Which ones actually improved your life this month?"
        }
        return templates.get(pattern_code, "What pattern do you notice in your spending, and what does it tell you?")

question_generator = QuestionGenerator()