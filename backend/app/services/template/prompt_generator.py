"""
Prompt template generator for LLMs based on style analysis
Creates personalized prompts that match user's writing style
"""

import logging
from datetime import datetime
from typing import Dict, Any, List

from app.models.template import StyleAnalysis, PromptTemplate
from app.models.llm import RecapTone, RecapLength

logger = logging.getLogger(__name__)


class PromptGenerator:
    """Service for generating LLM prompt templates based on style analysis"""
    
    def __init__(self):
        # Base prompt templates for different tones
        self.base_prompts = {
            RecapTone.PROFESSIONAL: {
                "system": "You are a professional fantasy football analyst writing detailed weekly recaps.",
                "style_base": "Write in a professional, analytical tone with clear structure and objective analysis."
            },
            RecapTone.HUMOROUS: {
                "system": "You are a witty fantasy football writer who creates entertaining weekly recaps with humor and personality.",
                "style_base": "Write with humor, wit, and entertaining commentary while maintaining accuracy."
            },
            RecapTone.DRAMATIC: {
                "system": "You are a dramatic fantasy football storyteller who brings excitement and emotion to weekly recaps.",
                "style_base": "Write with dramatic flair, emotional language, and compelling narratives."
            },
            RecapTone.CASUAL: {
                "system": "You are a friendly fantasy football enthusiast writing casual weekly recaps for friends.",
                "style_base": "Write in a casual, conversational tone as if talking to friends."
            }
        }
        
        # Structure templates
        self.structure_templates = {
            "intro_conclusion": """
Structure your recap as follows:
1. Opening introduction that sets the tone for the week
2. Main content covering key performances and storylines
3. Concluding wrap-up with forward-looking statements

{content_sections}

4. Conclusion that summarizes the week and looks ahead
""",
            "no_intro": """
Structure your recap as follows:
1. Jump directly into the main content
2. Cover key performances and storylines

{content_sections}

3. End with summary or forward-looking statements
""",
            "simple": """
Structure your recap as follows:
1. Main content covering performances and storylines

{content_sections}
""",
            "with_headers": """
Structure your recap with clear sections:

## Week Overview
Brief introduction to the week's action

## Top Performers
{winners_section}

## Disappointments
{losers_section}

{awards_section}

{predictions_section}
"""
        }
    
    def generate_prompt_template(
        self, 
        template_id: str,
        user_id: str,
        analysis: StyleAnalysis
    ) -> PromptTemplate:
        """
        Generate a personalized prompt template based on style analysis
        
        Args:
            template_id: ID of the source template
            user_id: User ID
            analysis: Style analysis results
            
        Returns:
            PromptTemplate: Generated prompt template
        """
        # Generate system prompt
        system_prompt = self._generate_system_prompt(analysis)
        
        # Generate style instructions
        style_instructions = self._generate_style_instructions(analysis)
        
        # Generate structure template
        structure_template = self._generate_structure_template(analysis)
        
        return PromptTemplate(
            template_id=template_id,
            user_id=user_id,
            system_prompt=system_prompt,
            style_instructions=style_instructions,
            structure_template=structure_template,
            based_on_analysis=analysis,
            generated_at=datetime.utcnow()
        )
    
    def _generate_system_prompt(self, analysis: StyleAnalysis) -> str:
        """Generate system-level prompt based on analysis"""
        base_system = self.base_prompts[analysis.tone]["system"]
        
        # Add personality based on analysis
        personality_traits = []
        
        if analysis.humor_level > 0.3:
            personality_traits.append("You use humor and entertaining commentary")
        
        if analysis.formality_level > 0.6:
            personality_traits.append("You maintain a professional and formal tone")
        elif analysis.formality_level < 0.3:
            personality_traits.append("You write in a casual, conversational style")
        
        if analysis.emotion_intensity > 0.5:
            personality_traits.append("You express emotions and excitement in your writing")
        
        if analysis.use_of_statistics:
            personality_traits.append("You incorporate statistics and data analysis")
        
        if analysis.use_of_metaphors:
            personality_traits.append("You use creative metaphors and comparisons")
        
        if analysis.mentions_specific_players:
            personality_traits.append("You frequently mention specific players and their performances")
        
        # Combine base with personality
        if personality_traits:
            personality_text = " ".join(personality_traits) + "."
            system_prompt = f"{base_system} {personality_text}"
        else:
            system_prompt = base_system
        
        return system_prompt
    
    def _generate_style_instructions(self, analysis: StyleAnalysis) -> str:
        """Generate detailed style instructions"""
        instructions = []
        
        # Base style from tone
        instructions.append(self.base_prompts[analysis.tone]["style_base"])
        
        # Sentence length guidance
        if analysis.avg_sentence_length > 20:
            instructions.append("Use longer, more complex sentences with detailed explanations.")
        elif analysis.avg_sentence_length < 10:
            instructions.append("Keep sentences short and punchy for easy reading.")
        else:
            instructions.append("Use a mix of short and medium-length sentences for good flow.")
        
        # Vocabulary complexity
        if analysis.vocabulary_complexity > 0.6:
            instructions.append("Use sophisticated vocabulary and complex expressions.")
        elif analysis.vocabulary_complexity < 0.4:
            instructions.append("Use simple, accessible language that everyone can understand.")
        else:
            instructions.append("Balance simple and sophisticated language appropriately.")
        
        # Humor level
        if analysis.humor_level > 0.4:
            instructions.append("Include jokes, puns, and entertaining commentary throughout.")
        elif analysis.humor_level > 0.2:
            instructions.append("Add occasional humor and light-hearted moments.")
        
        # Emotion intensity
        if analysis.emotion_intensity > 0.6:
            instructions.append("Express strong emotions and excitement about performances.")
            instructions.append("Use exclamation points and emotional language when appropriate.")
        elif analysis.emotion_intensity < 0.3:
            instructions.append("Maintain a calm, measured tone throughout.")
        
        # Statistical usage
        if analysis.use_of_statistics:
            instructions.append("Include relevant statistics, projections, and data analysis.")
        
        # Metaphor usage
        if analysis.use_of_metaphors:
            instructions.append("Use creative metaphors and comparisons to make points memorable.")
        
        # Signature phrases (if available)
        if analysis.common_phrases:
            phrases = ", ".join(analysis.common_phrases[:3])
            instructions.append(f"Try to incorporate phrases similar to: {phrases}")
        
        # Personal pronouns based on writing patterns
        if analysis.writing_patterns.get("uses_first_person"):
            instructions.append("Write from a personal perspective using 'I' and 'my' when appropriate.")
        
        if analysis.writing_patterns.get("uses_second_person"):
            instructions.append("Address readers directly using 'you' and 'your'.")
        
        return "\n".join(f"- {instruction}" for instruction in instructions)
    
    def _generate_structure_template(self, analysis: StyleAnalysis) -> str:
        """Generate structure template based on analysis"""
        # Determine structure type
        if analysis.uses_headers:
            template_key = "with_headers"
        elif analysis.has_intro and analysis.has_conclusion:
            template_key = "intro_conclusion"
        elif analysis.has_intro and not analysis.has_conclusion:
            template_key = "no_intro"
        else:
            template_key = "simple"
        
        base_structure = self.structure_templates[template_key]
        
        # Generate content sections based on focus patterns
        content_sections = []
        
        if analysis.focuses_on_winners:
            content_sections.append("- Highlight top performers and standout plays")
        
        if analysis.focuses_on_losers:
            content_sections.append("- Address disappointments and underperformances")
        
        if analysis.mentions_specific_players:
            content_sections.append("- Mention specific players and their contributions")
        
        if analysis.includes_awards:
            content_sections.append("- Include weekly awards and recognitions")
        
        if analysis.includes_predictions:
            content_sections.append("- Provide predictions or outlook for upcoming games")
        
        # Default content if no specific patterns found
        if not content_sections:
            content_sections = [
                "- Cover key matchups and results",
                "- Highlight notable performances",
                "- Provide analysis and insights"
            ]
        
        # Format the template
        if template_key == "with_headers":
            # Special formatting for header-based structure
            winners_section = "Highlight the week's best performances" if analysis.focuses_on_winners else "Cover strong performances"
            losers_section = "Address disappointing performances" if analysis.focuses_on_losers else "Mention underperformances if relevant"
            awards_section = "## Weekly Awards\nPresent any weekly awards or recognitions" if analysis.includes_awards else ""
            predictions_section = "## Looking Ahead\nProvide predictions for next week" if analysis.includes_predictions else ""
            
            return base_structure.format(
                winners_section=winners_section,
                losers_section=losers_section,
                awards_section=awards_section,
                predictions_section=predictions_section
            ).strip()
        else:
            # Standard formatting
            content_text = "\n".join(content_sections)
            return base_structure.format(content_sections=content_text)
    
    def generate_recap_prompt(
        self, 
        prompt_template: PromptTemplate,
        league_data: Dict[str, Any],
        week: int,
        season: int,
        length: RecapLength = RecapLength.MEDIUM
    ) -> str:
        """
        Generate a complete recap prompt using the template
        
        Args:
            prompt_template: User's personalized prompt template
            league_data: Fantasy league data for the week
            week: Week number
            season: Season year
            length: Desired recap length
            
        Returns:
            str: Complete prompt for LLM
        """
        # Length-specific instructions
        length_instructions = {
            RecapLength.SHORT: "Keep the recap concise and focused (300-500 words).",
            RecapLength.MEDIUM: "Write a comprehensive recap (500-800 words).",
            RecapLength.LONG: "Create a detailed, thorough recap (800+ words)."
        }
        
        # Build the complete prompt
        prompt_parts = [
            f"SYSTEM: {prompt_template.system_prompt}",
            "",
            "STYLE INSTRUCTIONS:",
            prompt_template.style_instructions,
            "",
            "STRUCTURE:",
            prompt_template.structure_template,
            "",
            f"LENGTH: {length_instructions[length]}",
            "",
            f"DATA FOR WEEK {week}, {season}:",
            str(league_data),  # In practice, this would be formatted nicely
            "",
            f"Write a fantasy football recap for Week {week} of the {season} season using the provided data. Follow the style and structure guidelines above to match the user's preferred writing style."
        ]
        
        return "\n".join(prompt_parts)


# Global instance
prompt_generator = PromptGenerator()
