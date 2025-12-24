"""
Match Service Module

Handles calculation of match scores between loan applications and lenders using LLM.
"""
import logging
import json
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
import os

# Configure logging
logger = logging.getLogger(__name__)


class MatchService:
    """
    Service class for calculating match scores between loan applications and lenders.
    
    This service uses OpenAI's GPT models to analyze loan applications against
    lender policies and calculate match scores.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2
    ):
        """
        Initialize Match Service
        
        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var
            model: OpenAI model to use (default: gpt-4o-mini)
            temperature: Temperature for generation (default: 0.2 for more deterministic output)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI API key not provided. Match score calculation will fail.")
        
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
        self.model = model
        self.temperature = temperature
        
        logger.info(f"Match Service initialized with model: {model}")
    
    def _build_match_prompt(
        self,
        application_data: Dict[str, Any],
        lender_data: Dict[str, Any],
        lender_name: str
    ) -> str:
        """
        Build the prompt for match score calculation.
        
        Args:
            application_data: Processed loan application data
            lender_data: Processed lender policy data
            lender_name: Name of the lender
        
        Returns:
            str: Formatted prompt for the LLM
        """
        prompt = f"""You are a financial matching expert. Your task is to analyze a loan application against a lender's policy and calculate a match score.

Lender: {lender_name}

Lender Policy Data:
{json.dumps(lender_data, indent=2)}

Loan Application Data:
{json.dumps(application_data, indent=2)}

Please analyze the match between this loan application and the lender's policy, considering:
1. **Loan Amount**: Does the requested amount fall within the lender's range?
2. **Loan Type**: Does the lender offer the type of loan requested?
3. **Interest Rate**: Are the applicant's expectations aligned with the lender's rates?
4. **Eligibility Criteria**: Does the applicant meet the lender's requirements?
5. **Tenure**: Is the requested loan tenure available?
6. **Credit Profile**: Does the applicant's credit profile match the lender's criteria?
7. **Income Requirements**: Does the applicant meet income requirements?
8. **Documentation**: Can the applicant provide required documents?
9. **Special Conditions**: Are there any special conditions that affect the match?
10. **Overall Fit**: General compatibility between application and lender policy

Calculate a match score from 0-100 where:
- 90-100: Excellent match, highly recommended
- 75-89: Very good match, recommended
- 60-74: Good match, suitable
- 40-59: Fair match, possible with conditions
- 20-39: Poor match, significant gaps
- 0-19: Very poor match, not recommended

Return ONLY a valid JSON object with the following structure:
{{
    "match_score": <number between 0-100>,
    "match_category": "<excellent|very_good|good|fair|poor|very_poor>",
    "strengths": ["<list of matching strengths>"],
    "weaknesses": ["<list of matching weaknesses>"],
    "recommendations": ["<list of recommendations for the applicant>"],
    "criteria_scores": {{
        "loan_amount": <0-10>,
        "loan_type": <0-10>,
        "interest_rate": <0-10>,
        "eligibility": <0-10>,
        "tenure": <0-10>,
        "credit_profile": <0-10>,
        "income": <0-10>,
        "documentation": <0-10>,
        "special_conditions": <0-10>,
        "overall_fit": <0-10>
    }},
    "summary": "<brief summary of the match analysis>"
}}

Be objective and thorough in your analysis. Consider both positive and negative aspects.
"""
        return prompt
    
    async def calculate_match_score(
        self,
        application_data: Dict[str, Any],
        lender_data: Dict[str, Any],
        lender_name: str,
        application_id: int,
        lender_id: int
    ) -> Dict[str, Any]:
        """
        Calculate match score between a loan application and a lender.
        
        Args:
            application_data: Processed loan application data
            lender_data: Processed lender policy data
            lender_name: Name of the lender
            application_id: ID of the loan application
            lender_id: ID of the lender
        
        Returns:
            Dict[str, Any]: Match analysis including score and detailed breakdown
            
        Raises:
            RuntimeError: If match calculation fails
            ValueError: If API key is not configured
        """
        try:
            logger.info(
                f"Calculating match score for Application ID {application_id} "
                f"against Lender ID {lender_id} ({lender_name})"
            )
            
            # Validate client
            if not self.client:
                logger.error("OpenAI client not initialized. API key missing.")
                raise ValueError("OpenAI API key not configured")
            
            # Validate input data
            if not application_data:
                logger.error("Empty application data provided")
                raise ValueError("Application data is empty")
            
            if not lender_data:
                logger.error("Empty lender data provided")
                raise ValueError("Lender data is empty")
            
            # Build prompt
            prompt = self._build_match_prompt(application_data, lender_data, lender_name)
            
            logger.debug(f"Sending match calculation request to OpenAI (model: {self.model})")
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial matching expert specialized in analyzing loan applications against lender policies and calculating accurate match scores."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            # Extract response
            content = response.choices[0].message.content
            
            logger.debug(f"Received match analysis from OpenAI: {len(content)} characters")
            
            # Parse JSON response
            try:
                match_analysis = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse match analysis as JSON: {str(e)}")
                # Fallback: return default low score
                match_analysis = {
                    "match_score": 0,
                    "match_category": "error",
                    "error": "Failed to parse response",
                    "raw_response": content
                }
            
            # Add metadata
            match_analysis["_metadata"] = {
                "model": self.model,
                "temperature": self.temperature,
                "tokens_used": response.usage.total_tokens,
                "application_id": application_id,
                "lender_id": lender_id,
                "lender_name": lender_name,
                "calculation_successful": True
            }
            
            # Extract match score for easy access
            match_score = match_analysis.get("match_score", 0)
            
            logger.info(
                f"Match calculation completed. Score: {match_score}/100. "
                f"Tokens used: {response.usage.total_tokens}"
            )
            
            return {
                "match_score": match_score,
                "match_analysis": match_analysis
            }
            
        except Exception as e:
            logger.error(
                f"Match calculation failed for Application {application_id} "
                f"and Lender {lender_id}: {str(e)}",
                exc_info=True
            )
            raise RuntimeError(f"Match calculation failed: {str(e)}") from e
    
    async def batch_calculate_matches(
        self,
        application_data: Dict[str, Any],
        lenders: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        """
        Calculate match scores for an application against multiple lenders.
        
        This method is useful for sequential processing, but for parallel processing,
        use Hatchet workflows instead.
        
        Args:
            application_data: Processed loan application data
            lenders: List of lender dictionaries with 'id', 'name', and 'data' keys
        
        Returns:
            List of match results
        """
        logger.info(f"Batch calculating matches against {len(lenders)} lenders")
        
        results = []
        for lender in lenders:
            try:
                result = await self.calculate_match_score(
                    application_data=application_data,
                    lender_data=lender.get("data", {}),
                    lender_name=lender.get("name", "Unknown"),
                    application_id=lender.get("application_id", 0),
                    lender_id=lender.get("id", 0)
                )
                results.append({
                    "lender_id": lender.get("id"),
                    "success": True,
                    **result
                })
            except Exception as e:
                logger.error(f"Failed to calculate match for lender {lender.get('id')}: {str(e)}")
                results.append({
                    "lender_id": lender.get("id"),
                    "success": False,
                    "error": str(e)
                })
        
        logger.info(f"Batch calculation completed. {len(results)} results")
        return results

