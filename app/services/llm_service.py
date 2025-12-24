"""
LLM Service Module

Handles processing of raw OCR text into structured data using Large Language Models.
"""
import logging
import json
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
import os

# Configure logging
logger = logging.getLogger(__name__)


class LLMService:
    """
    Service class for LLM-based text processing.
    
    This service uses OpenAI's GPT models to convert raw OCR text
    into structured, processed data.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2
    ):
        """
        Initialize LLM Service
        
        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var
            model: OpenAI model to use (default: gpt-4o-mini)
            temperature: Temperature for generation (default: 0.2 for more deterministic output)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI API key not provided. LLM processing will fail.")
        
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
        self.model = model
        self.temperature = temperature
        
        logger.info(f"LLM Service initialized with model: {model}")
    
    def _build_processing_prompt(self, raw_text: str, lender_name: str) -> str:
        """
        Build the prompt for LLM processing.
        
        Args:
            raw_text: Raw OCR text to process
            lender_name: Name of the lender
        
        Returns:
            str: Formatted prompt for the LLM
        """
        prompt = f"""You are a financial document analysis expert. Your task is to analyze the following OCR-extracted text from a lender's policy document and extract structured information.

Lender Name: {lender_name}

Raw OCR Text:
{raw_text}

Please extract and structure the following information in JSON format:
1. **Loan Types**: List of loan types offered (e.g., personal, home, auto, business)
2. **Interest Rates**: Interest rate ranges or specific rates mentioned
3. **Eligibility Criteria**: Requirements for loan applicants
4. **Loan Amount Range**: Minimum and maximum loan amounts
5. **Tenure**: Loan repayment period options
6. **Processing Fees**: Any fees or charges mentioned
7. **Documents Required**: List of documents needed for loan application
8. **Key Terms and Conditions**: Important T&Cs from the policy
9. **Contact Information**: Phone numbers, email, website, addresses
10. **Special Offers**: Any promotional offers or special schemes

Return ONLY a valid JSON object with these keys. If information is not found, use null for that field.
Ensure all extracted text is clean, properly formatted, and accurate.

Example output format:
{{
    "loan_types": ["personal", "home"],
    "interest_rates": {{"min": "10.5%", "max": "15.0%"}},
    "eligibility_criteria": ["Age 21-65", "Minimum income Rs. 25,000"],
    "loan_amount_range": {{"min": "Rs. 50,000", "max": "Rs. 20,00,000"}},
    "tenure": {{"min": "12 months", "max": "60 months"}},
    "processing_fees": "2% of loan amount",
    "documents_required": ["PAN Card", "Aadhaar Card", "Bank Statements"],
    "key_terms": ["Prepayment allowed after 6 months", "No collateral required"],
    "contact_information": {{
        "phone": "+91-XXXXXXXXXX",
        "email": "info@lender.com",
        "website": "www.lender.com"
    }},
    "special_offers": ["0.5% discount on interest for salaried employees"]
}}
"""
        return prompt
    
    async def process_raw_text(
        self,
        raw_text: str,
        lender_name: str,
        policy_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process raw OCR text using LLM to extract structured information.
        
        Args:
            raw_text: Raw OCR-extracted text
            lender_name: Name of the lender
            policy_details: Optional existing policy details for context
        
        Returns:
            Dict[str, Any]: Structured data extracted by LLM
            
        Raises:
            RuntimeError: If LLM processing fails
            ValueError: If API key is not configured
        """
        try:
            logger.info(f"Starting LLM processing for lender: {lender_name}")
            
            # Validate client
            if not self.client:
                logger.error("OpenAI client not initialized. API key missing.")
                raise ValueError("OpenAI API key not configured")
            
            # Validate input
            if not raw_text or not raw_text.strip():
                logger.error("Empty raw text provided for processing")
                raise ValueError("Raw text is empty")
            
            # Build prompt
            prompt = self._build_processing_prompt(raw_text, lender_name)
            
            logger.debug(f"Sending request to OpenAI (model: {self.model})")
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial document analysis expert specialized in extracting structured information from loan policy documents."
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
            
            logger.debug(f"Received response from OpenAI: {len(content)} characters")
            
            # Parse JSON response
            try:
                processed_data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
                # Fallback: return raw content in a structured format
                processed_data = {
                    "error": "Failed to parse response",
                    "raw_response": content
                }
            
            # Add metadata
            processed_data["_metadata"] = {
                "model": self.model,
                "temperature": self.temperature,
                "tokens_used": response.usage.total_tokens,
                "processing_successful": True
            }
            
            logger.info(
                f"LLM processing completed successfully. "
                f"Tokens used: {response.usage.total_tokens}"
            )
            
            return processed_data
            
        except Exception as e:
            logger.error(f"LLM processing failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"LLM processing failed: {str(e)}") from e
    
    async def validate_and_enrich_data(
        self,
        processed_data: Dict[str, Any],
        raw_text: str
    ) -> Dict[str, Any]:
        """
        Validate and potentially enrich processed data.
        
        Args:
            processed_data: Already processed data
            raw_text: Original raw text for validation
        
        Returns:
            Dict[str, Any]: Validated and enriched data
        """
        try:
            logger.info("Validating and enriching processed data")
            
            # Add confidence scores or validation flags
            enriched_data = processed_data.copy()
            
            # Simple validation: check if key fields exist
            required_fields = [
                "loan_types", "interest_rates", "eligibility_criteria"
            ]
            
            validation_status = {
                field: field in processed_data and processed_data[field] is not None
                for field in required_fields
            }
            
            enriched_data["_validation"] = {
                "field_completeness": validation_status,
                "completeness_score": sum(validation_status.values()) / len(required_fields)
            }
            
            logger.info(
                f"Validation completed. "
                f"Completeness score: {enriched_data['_validation']['completeness_score']:.2%}"
            )
            
            return enriched_data
            
        except Exception as e:
            logger.warning(f"Validation/enrichment failed: {str(e)}")
            # Return original data if enrichment fails
            return processed_data
    
    def _build_loan_application_prompt(self, raw_text: str, applicant_name: str) -> str:
        """
        Build the prompt for loan application processing.
        
        Args:
            raw_text: Raw OCR text from loan application
            applicant_name: Name of the applicant
        
        Returns:
            str: Formatted prompt for the LLM
        """
        prompt = f"""You are a loan application analysis expert. Your task is to analyze the following OCR-extracted text from a loan application and extract structured information.

Applicant Name: {applicant_name}

Raw OCR Text:
{raw_text}

Please extract and structure the following information in JSON format:
1. **Loan Type**: Type of loan requested (e.g., personal, home, auto, business)
2. **Loan Amount**: Amount of loan requested
3. **Loan Purpose**: Purpose of the loan
4. **Tenure Requested**: Desired loan repayment period
5. **Employment Details**: Employment status, employer name, job title, years employed
6. **Income Details**: Monthly/annual income, other income sources
7. **Credit Score**: Credit score if mentioned
8. **Existing Loans**: Details of existing loans or debts
9. **Assets**: Property, vehicles, investments owned
10. **Personal Information**: Age, marital status, dependents, education
11. **Contact Information**: Phone, email, address
12. **Documents Provided**: List of documents submitted with application
13. **Special Requirements**: Any special conditions or requirements mentioned

Return ONLY a valid JSON object with these keys. If information is not found, use null for that field.
Ensure all extracted text is clean, properly formatted, and accurate.

Example output format:
{{
    "loan_type": "home",
    "loan_amount": {{"amount": 500000, "currency": "USD"}},
    "loan_purpose": "Purchase primary residence",
    "tenure_requested": {{"years": 30}},
    "employment_details": {{
        "status": "employed",
        "employer": "ABC Corp",
        "job_title": "Software Engineer",
        "years_employed": 5
    }},
    "income_details": {{
        "monthly_income": 8000,
        "annual_income": 96000,
        "other_income": null
    }},
    "credit_score": 750,
    "existing_loans": [
        {{"type": "auto", "balance": 15000, "monthly_payment": 350}}
    ],
    "assets": {{
        "property": [],
        "vehicles": [{{"type": "car", "value": 25000}}],
        "investments": {{"stocks": 50000}}
    }},
    "personal_information": {{
        "age": 35,
        "marital_status": "married",
        "dependents": 2,
        "education": "Bachelor's Degree"
    }},
    "contact_information": {{
        "phone": "+1-XXX-XXX-XXXX",
        "email": "applicant@email.com",
        "address": "123 Main St, City, State ZIP"
    }},
    "documents_provided": ["Pay stubs", "Tax returns", "Bank statements"],
    "special_requirements": null
}}
"""
        return prompt
    
    async def process_loan_application(
        self,
        raw_text: str,
        applicant_name: str
    ) -> Dict[str, Any]:
        """
        Process raw OCR text from loan application using LLM to extract structured information.
        
        Args:
            raw_text: Raw OCR-extracted text from loan application
            applicant_name: Name of the applicant
        
        Returns:
            Dict[str, Any]: Structured application data extracted by LLM
            
        Raises:
            RuntimeError: If LLM processing fails
            ValueError: If API key is not configured
        """
        try:
            logger.info(f"Starting LLM processing for loan application: {applicant_name}")
            
            # Validate client
            if not self.client:
                logger.error("OpenAI client not initialized. API key missing.")
                raise ValueError("OpenAI API key not configured")
            
            # Validate input
            if not raw_text or not raw_text.strip():
                logger.error("Empty raw text provided for processing")
                raise ValueError("Raw text is empty")
            
            # Build prompt
            prompt = self._build_loan_application_prompt(raw_text, applicant_name)
            
            logger.info(f"Sending request to OpenAI (model: {self.model})")
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a loan application analysis expert specialized in extracting structured information from loan application documents."
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
            
            logger.info(f"Received response from OpenAI: {len(content)} characters")
            
            # Parse JSON response
            try:
                processed_data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
                # Fallback: return raw content in a structured format
                processed_data = {
                    "error": "Failed to parse response",
                    "raw_response": content
                }
            
            # Add metadata
            processed_data["_metadata"] = {
                "model": self.model,
                "temperature": self.temperature,
                "tokens_used": response.usage.total_tokens,
                "processing_successful": True
            }
            
            logger.info(
                f"LLM processing completed successfully. "
                f"Tokens used: {response.usage.total_tokens}"
            )
            
            return processed_data
            
        except Exception as e:
            logger.error(f"LLM processing failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"LLM processing failed: {str(e)}") from e

