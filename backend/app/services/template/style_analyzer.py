"""
Style analysis service for uploaded template files
Uses NLP techniques to analyze tone, style, and structure
"""

import re
import statistics
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter
from datetime import datetime

from app.models.template import StyleAnalysis
from app.models.llm import RecapTone

logger = logging.getLogger(__name__)


class StyleAnalyzer:
    """Service for analyzing writing style of uploaded templates"""
    
    def __init__(self):
        # Load word lists for analysis
        self._load_word_lists()
        
        # Sentiment indicators
        self.positive_words = {
            'amazing', 'awesome', 'fantastic', 'incredible', 'outstanding', 'phenomenal',
            'domination', 'crushed', 'destroyed', 'excellence', 'brilliant', 'stellar'
        }
        
        self.negative_words = {
            'terrible', 'awful', 'horrible', 'disaster', 'pathetic', 'embarrassing',
            'struggled', 'failed', 'disappointing', 'mediocre', 'underwhelming'
        }
        
        self.humor_indicators = {
            'lol', 'lmao', 'haha', 'rofl', 'savage', 'rekt', 'owned', 'boom',
            'mic drop', 'brutal', 'shots fired', 'trash', 'clown', 'jokes'
        }
        
        self.formal_indicators = {
            'furthermore', 'however', 'therefore', 'consequently', 'nevertheless',
            'moreover', 'additionally', 'subsequently', 'accordingly', 'hence'
        }
        
        self.statistical_phrases = {
            'projected', 'averaged', 'percentage', 'statistics', 'data', 'metrics',
            'analysis', 'trend', 'correlation', 'performance', 'efficiency'
        }
        
        self.metaphor_indicators = {
            'like a', 'as if', 'reminds me of', 'similar to', 'just like',
            'beast', 'monster', 'warrior', 'king', 'god', 'machine'
        }
    
    def _load_word_lists(self):
        """Load vocabulary complexity word lists"""
        # Simple vs complex word indicators
        self.simple_words = {
            'good', 'bad', 'big', 'small', 'nice', 'cool', 'great', 'fun',
            'easy', 'hard', 'fast', 'slow', 'hot', 'cold', 'new', 'old'
        }
        
        self.complex_words = {
            'exceptional', 'extraordinary', 'magnificent', 'sophisticated',
            'comprehensive', 'substantial', 'predominant', 'significant',
            'elaborate', 'intricate', 'prevalent', 'fundamental'
        }
    
    def analyze_style(self, text: str) -> StyleAnalysis:
        """
        Analyze the writing style of the given text
        
        Args:
            text: Text to analyze
            
        Returns:
            StyleAnalysis: Comprehensive style analysis
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Prepare text for analysis
        text_lower = text.lower()
        words = self._tokenize_words(text)
        sentences = self._split_sentences(text)
        paragraphs = self._split_paragraphs(text)
        
        # Perform various analyses
        tone_analysis = self._analyze_tone(text_lower, words)
        style_characteristics = self._analyze_style_characteristics(text_lower, words, sentences)
        writing_characteristics = self._analyze_writing_characteristics(words, sentences)
        structure_analysis = self._analyze_structure(text, paragraphs)
        content_patterns = self._analyze_content_patterns(text_lower)
        linguistic_features = self._analyze_linguistic_features(text, words)
        
        # Combine all analyses
        return StyleAnalysis(
            # Tone analysis
            tone=tone_analysis["tone"],
            tone_confidence=tone_analysis["confidence"],
            
            # Style characteristics
            formality_level=style_characteristics["formality_level"],
            humor_level=style_characteristics["humor_level"],
            emotion_intensity=style_characteristics["emotion_intensity"],
            
            # Writing characteristics
            avg_sentence_length=writing_characteristics["avg_sentence_length"],
            vocabulary_complexity=writing_characteristics["vocabulary_complexity"],
            use_of_metaphors=writing_characteristics["use_of_metaphors"],
            use_of_statistics=writing_characteristics["use_of_statistics"],
            
            # Structure analysis
            has_intro=structure_analysis["has_intro"],
            has_conclusion=structure_analysis["has_conclusion"],
            uses_headers=structure_analysis["uses_headers"],
            paragraph_count=structure_analysis["paragraph_count"],
            
            # Content patterns
            focuses_on_winners=content_patterns["focuses_on_winners"],
            focuses_on_losers=content_patterns["focuses_on_losers"],
            includes_predictions=content_patterns["includes_predictions"],
            includes_awards=content_patterns["includes_awards"],
            mentions_specific_players=content_patterns["mentions_specific_players"],
            
            # Linguistic features
            common_phrases=linguistic_features["common_phrases"],
            signature_words=linguistic_features["signature_words"],
            writing_patterns=linguistic_features["writing_patterns"]
        )
    
    def _tokenize_words(self, text: str) -> List[str]:
        """Extract words from text"""
        # Simple tokenization - split on whitespace and punctuation
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return words
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs"""
        paragraphs = text.split('\n\n')
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _analyze_tone(self, text_lower: str, words: List[str]) -> Dict[str, Any]:
        """Analyze the tone of the text"""
        # Count tone indicators
        positive_count = sum(1 for word in self.positive_words if word in text_lower)
        negative_count = sum(1 for word in self.negative_words if word in text_lower)
        humor_count = sum(1 for word in self.humor_indicators if word in text_lower)
        formal_count = sum(1 for word in self.formal_indicators if word in text_lower)
        
        # Calculate scores
        total_words = len(words)
        if total_words == 0:
            return {"tone": RecapTone.PROFESSIONAL, "confidence": 0.5}
        
        humor_score = humor_count / total_words * 100
        formal_score = formal_count / total_words * 100
        emotion_score = (positive_count + negative_count) / total_words * 100
        
        # Determine primary tone
        if humor_score > 0.5:
            tone = RecapTone.HUMOROUS
            confidence = min(0.8, 0.5 + humor_score / 10)
        elif formal_score > 0.3:
            tone = RecapTone.PROFESSIONAL
            confidence = min(0.8, 0.5 + formal_score / 10)
        elif emotion_score > 1.0:
            tone = RecapTone.DRAMATIC
            confidence = min(0.8, 0.5 + emotion_score / 20)
        else:
            tone = RecapTone.CASUAL
            confidence = 0.6
        
        return {"tone": tone, "confidence": confidence}
    
    def _analyze_style_characteristics(self, text_lower: str, words: List[str], sentences: List[str]) -> Dict[str, float]:
        """Analyze style characteristics"""
        total_words = len(words)
        
        # Formality level
        formal_count = sum(1 for word in self.formal_indicators if word in text_lower)
        casual_markers = text_lower.count("'") + text_lower.count("gonna") + text_lower.count("wanna")
        formality_level = min(1.0, max(0.0, (formal_count / total_words * 10) - (casual_markers / total_words * 5)))
        
        # Humor level
        humor_count = sum(1 for word in self.humor_indicators if word in text_lower)
        humor_level = min(1.0, humor_count / total_words * 20)
        
        # Emotion intensity
        emotional_words = sum(1 for word in (self.positive_words | self.negative_words) if word in text_lower)
        exclamation_count = text_lower.count('!')
        caps_count = sum(1 for sentence in sentences if any(word.isupper() for word in sentence.split()))
        emotion_intensity = min(1.0, (emotional_words / total_words * 10) + (exclamation_count / len(sentences)) + (caps_count / len(sentences)))
        
        return {
            "formality_level": formality_level,
            "humor_level": humor_level,
            "emotion_intensity": emotion_intensity
        }
    
    def _analyze_writing_characteristics(self, words: List[str], sentences: List[str]) -> Dict[str, Any]:
        """Analyze writing characteristics"""
        if not sentences:
            return {
                "avg_sentence_length": 0,
                "vocabulary_complexity": 0,
                "use_of_metaphors": False,
                "use_of_statistics": False
            }
        
        # Average sentence length
        sentence_lengths = [len(sentence.split()) for sentence in sentences]
        avg_sentence_length = statistics.mean(sentence_lengths)
        
        # Vocabulary complexity
        complex_word_count = sum(1 for word in words if word in self.complex_words)
        simple_word_count = sum(1 for word in words if word in self.simple_words)
        
        if complex_word_count + simple_word_count > 0:
            vocabulary_complexity = complex_word_count / (complex_word_count + simple_word_count)
        else:
            vocabulary_complexity = 0.5  # Default middle value
        
        # Metaphor usage
        text_full = ' '.join(sentences).lower()
        use_of_metaphors = any(indicator in text_full for indicator in self.metaphor_indicators)
        
        # Statistics usage
        use_of_statistics = any(phrase in text_full for phrase in self.statistical_phrases)
        
        return {
            "avg_sentence_length": avg_sentence_length,
            "vocabulary_complexity": vocabulary_complexity,
            "use_of_metaphors": use_of_metaphors,
            "use_of_statistics": use_of_statistics
        }
    
    def _analyze_structure(self, text: str, paragraphs: List[str]) -> Dict[str, Any]:
        """Analyze text structure"""
        # Check for introduction patterns
        intro_patterns = [
            r"welcome", r"this week", r"week \d+", r"let's dive", r"recap time",
            r"another week", r"time to", r"it's time"
        ]
        has_intro = any(re.search(pattern, paragraphs[0].lower()) for pattern in intro_patterns) if paragraphs else False
        
        # Check for conclusion patterns
        conclusion_patterns = [
            r"in conclusion", r"to wrap up", r"that's all", r"until next",
            r"see you next", r"final thoughts", r"looking ahead"
        ]
        has_conclusion = any(re.search(pattern, paragraphs[-1].lower()) for pattern in conclusion_patterns) if paragraphs else False
        
        # Check for headers (simple check for lines that are short and potentially headers)
        uses_headers = bool(re.search(r'^[A-Z][A-Za-z\s]{2,30}:?\s*$', text, re.MULTILINE))
        
        return {
            "has_intro": has_intro,
            "has_conclusion": has_conclusion,
            "uses_headers": uses_headers,
            "paragraph_count": len(paragraphs)
        }
    
    def _analyze_content_patterns(self, text_lower: str) -> Dict[str, bool]:
        """Analyze content patterns specific to fantasy football"""
        # Winner focus patterns
        winner_patterns = [
            "dominated", "crushed", "destroyed", "amazing week", "fantastic performance",
            "star of the week", "mvp", "player of the week", "unstoppable"
        ]
        focuses_on_winners = any(pattern in text_lower for pattern in winner_patterns)
        
        # Loser focus patterns
        loser_patterns = [
            "disappointed", "struggled", "worst week", "failure", "let down",
            "bench", "dropped the ball", "awful performance", "disaster"
        ]
        focuses_on_losers = any(pattern in text_lower for pattern in loser_patterns)
        
        # Prediction patterns
        prediction_patterns = [
            "next week", "looking ahead", "prediction", "expect", "should bounce back",
            "likely to", "forecast", "upcoming", "projected"
        ]
        includes_predictions = any(pattern in text_lower for pattern in prediction_patterns)
        
        # Awards patterns
        award_patterns = [
            "award", "winner", "champion", "best", "worst", "most", "least",
            "player of", "performance of", "play of", "disappointment of"
        ]
        includes_awards = any(pattern in text_lower for pattern in award_patterns)
        
        # Player mention patterns (basic check for common NFL positions/names)
        player_patterns = [
            "quarterback", "qb", "running back", "rb", "wide receiver", "wr",
            "tight end", "te", "defense", "dst", "kicker", "mahomes", "allen",
            "jackson", "herbert", "burrow"  # Add common player names
        ]
        mentions_specific_players = any(pattern in text_lower for pattern in player_patterns)
        
        return {
            "focuses_on_winners": focuses_on_winners,
            "focuses_on_losers": focuses_on_losers,
            "includes_predictions": includes_predictions,
            "includes_awards": includes_awards,
            "mentions_specific_players": mentions_specific_players
        }
    
    def _analyze_linguistic_features(self, text: str, words: List[str]) -> Dict[str, Any]:
        """Analyze linguistic features and patterns"""
        # Find common phrases (2-3 word combinations)
        text_lower = text.lower()
        
        # Extract 2-word phrases
        two_word_phrases = []
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            two_word_phrases.append(phrase)
        
        # Extract 3-word phrases
        three_word_phrases = []
        for i in range(len(words) - 2):
            phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
            three_word_phrases.append(phrase)
        
        # Get most common phrases
        phrase_counter = Counter(two_word_phrases + three_word_phrases)
        common_phrases = [phrase for phrase, count in phrase_counter.most_common(10) if count > 1]
        
        # Find signature words (words used more frequently than typical)
        word_counter = Counter(words)
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'was', 'are', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
        
        signature_words = [
            word for word, count in word_counter.most_common(20)
            if word not in stop_words and len(word) > 3 and count > 1
        ]
        
        # Analyze writing patterns
        writing_patterns = {
            "avg_word_length": statistics.mean([len(word) for word in words]) if words else 0,
            "question_count": text.count('?'),
            "exclamation_count": text.count('!'),
            "ellipsis_count": text.count('...'),
            "parentheses_count": text.count('('),
            "quotes_count": text.count('"'),
            "uses_first_person": any(word in text_lower for word in ['i ', 'my ', 'me ', 'myself']),
            "uses_second_person": any(word in text_lower for word in ['you ', 'your ', 'yourself']),
            "uses_contractions": "'" in text
        }
        
        return {
            "common_phrases": common_phrases[:5],  # Top 5 phrases
            "signature_words": signature_words[:10],  # Top 10 signature words
            "writing_patterns": writing_patterns
        }


# Global instance
style_analyzer = StyleAnalyzer()
