#!/usr/bin/env python3
"""
Demo Script for Loan Application Feature

This script demonstrates the complete loan application workflow:
1. Upload a loan application PDF
2. Monitor processing status
3. Retrieve and display match results

Usage:
    python demo_loan_application.py path/to/application.pdf

Requirements:
    - API server running on http://localhost:8000
    - At least one lender with status=completed in database
    - PDF file to upload

Documentation:
    - Quick Start: docs/LOAN_APPLICATION_QUICKSTART.md
    - Examples: docs/LOAN_APPLICATION_EXAMPLES.md
    - Architecture: docs/LOAN_APPLICATION_FLOW.md
"""

import sys
import time
import requests
from typing import Dict, List, Optional
from pathlib import Path


class LoanApplicationDemo:
    """Demo client for loan application API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def upload_application(
        self,
        pdf_path: str,
        applicant_name: str,
        applicant_email: str,
        applicant_phone: Optional[str] = None
    ) -> Dict:
        """Upload a loan application PDF"""
        
        print(f"📄 Uploading loan application: {pdf_path}")
        
        url = f"{self.base_url}/api/loan-applications/upload"
        
        with open(pdf_path, 'rb') as f:
            files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
            data = {
                'applicant_name': applicant_name,
                'applicant_email': applicant_email
            }
            
            if applicant_phone:
                data['applicant_phone'] = applicant_phone
            
            response = self.session.post(url, files=files, data=data)
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Upload successful!")
            print(f"   Application ID: {result['application_id']}")
            print(f"   Status: {result['status']}")
            print(f"   Workflow Run ID: {result.get('workflow_run_id', 'N/A (mock mode)')}")
            
            return result
    
    def get_application(self, application_id: int) -> Dict:
        """Get application details"""
        
        url = f"{self.base_url}/api/loan-applications/{application_id}"
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def get_matches(
        self,
        application_id: int,
        min_score: Optional[float] = None
    ) -> List[Dict]:
        """Get match results for an application"""
        
        url = f"{self.base_url}/api/loan-applications/{application_id}/matches"
        params = {}
        
        if min_score is not None:
            params['min_score'] = min_score
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def wait_for_completion(
        self,
        application_id: int,
        max_wait: int = 60,
        poll_interval: int = 2
    ) -> str:
        """Wait for application processing to complete"""
        
        print(f"\n⏳ Waiting for processing to complete...")
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            app = self.get_application(application_id)
            status = app['status']
            
            print(f"   Status: {status}", end='\r')
            
            if status == 'completed':
                print(f"\n✅ Processing completed!")
                return status
            elif status == 'failed':
                print(f"\n❌ Processing failed!")
                return status
            
            time.sleep(poll_interval)
        
        print(f"\n⚠️  Timeout waiting for completion")
        return 'timeout'
    
    def display_matches(self, matches: List[Dict]):
        """Display match results in a formatted way"""
        
        if not matches:
            print("\n⚠️  No matches found")
            return
        
        print(f"\n📊 Match Results ({len(matches)} lenders)")
        print("=" * 80)
        
        for i, match in enumerate(matches, 1):
            score = match.get('match_score', 0)
            status = match['status']
            
            if status != 'completed':
                print(f"\n{i}. Lender {match['lender_id']} - Status: {status}")
                if match.get('error_message'):
                    print(f"   Error: {match['error_message']}")
                continue
            
            analysis = match.get('match_analysis', {})
            category = analysis.get('match_category', 'unknown')
            
            # Score bar
            bar_length = 40
            filled = int((score / 100) * bar_length)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            print(f"\n{i}. Lender {match['lender_id']}")
            print(f"   Score: {score:.1f}/100 [{bar}]")
            print(f"   Category: {category.upper().replace('_', ' ')}")
            
            # Strengths
            strengths = analysis.get('strengths', [])
            if strengths:
                print(f"\n   ✅ Strengths:")
                for strength in strengths[:3]:  # Show top 3
                    print(f"      • {strength}")
            
            # Weaknesses
            weaknesses = analysis.get('weaknesses', [])
            if weaknesses:
                print(f"\n   ⚠️  Weaknesses:")
                for weakness in weaknesses[:3]:  # Show top 3
                    print(f"      • {weakness}")
            
            # Recommendations
            recommendations = analysis.get('recommendations', [])
            if recommendations:
                print(f"\n   💡 Recommendations:")
                for rec in recommendations[:2]:  # Show top 2
                    print(f"      • {rec}")
            
            # Summary
            summary = analysis.get('summary', '')
            if summary:
                print(f"\n   📝 Summary: {summary}")
        
        print("\n" + "=" * 80)
    
    def run_demo(
        self,
        pdf_path: str,
        applicant_name: str,
        applicant_email: str,
        wait_for_processing: bool = True
    ):
        """Run complete demo workflow"""
        
        print("\n" + "=" * 80)
        print("🚀 Loan Application Demo")
        print("=" * 80)
        
        try:
            # Step 1: Upload
            result = self.upload_application(
                pdf_path=pdf_path,
                applicant_name=applicant_name,
                applicant_email=applicant_email
            )
            
            application_id = result['application_id']
            
            # Step 2: Wait for processing (if enabled)
            if wait_for_processing:
                status = self.wait_for_completion(application_id)
                
                if status == 'failed':
                    print("\n❌ Processing failed. Check logs for details.")
                    return
                elif status == 'timeout':
                    print("\n⚠️  Processing is taking longer than expected.")
                    print("   You can check status later using:")
                    print(f"   curl http://localhost:8000/api/loan-applications/{application_id}")
                    return
            else:
                print("\n⏭️  Skipping wait (processing in background)")
            
            # Step 3: Get matches
            print(f"\n🔍 Fetching match results...")
            matches = self.get_matches(application_id)
            
            # Step 4: Display results
            self.display_matches(matches)
            
            # Step 5: Show best matches
            completed_matches = [m for m in matches if m['status'] == 'completed']
            if completed_matches:
                best_match = max(completed_matches, key=lambda x: x.get('match_score', 0))
                print(f"\n🏆 Best Match: Lender {best_match['lender_id']} "
                      f"with score {best_match['match_score']:.1f}/100")
            
            # Step 6: Show API endpoints
            print(f"\n📚 Useful API Endpoints:")
            print(f"   View application: GET {self.base_url}/api/loan-applications/{application_id}")
            print(f"   View matches: GET {self.base_url}/api/loan-applications/{application_id}/matches")
            print(f"   Filter matches: GET {self.base_url}/api/loan-applications/{application_id}/matches?min_score=80")
            print(f"   API docs: {self.base_url}/docs")
            
            print("\n✅ Demo completed successfully!")
            
        except requests.exceptions.ConnectionError:
            print("\n❌ Error: Could not connect to API server")
            print("   Make sure the API server is running on http://localhost:8000")
            print("   Start it with: ./start_api.sh")
        except requests.exceptions.HTTPError as e:
            print(f"\n❌ HTTP Error: {e}")
            if e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"   Detail: {error_detail.get('detail', 'Unknown error')}")
                except:
                    print(f"   Response: {e.response.text}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point"""
    
    if len(sys.argv) < 2:
        print("Usage: python demo_loan_application.py <pdf_path> [applicant_name] [applicant_email]")
        print("\nExample:")
        print("  python demo_loan_application.py loan_application.pdf")
        print("  python demo_loan_application.py loan_application.pdf 'John Doe' 'john@example.com'")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    # Check if PDF exists
    if not Path(pdf_path).exists():
        print(f"❌ Error: File not found: {pdf_path}")
        sys.exit(1)
    
    # Get applicant details
    applicant_name = sys.argv[2] if len(sys.argv) > 2 else "Demo Applicant"
    applicant_email = sys.argv[3] if len(sys.argv) > 3 else "demo@example.com"
    
    # Run demo
    demo = LoanApplicationDemo()
    demo.run_demo(
        pdf_path=pdf_path,
        applicant_name=applicant_name,
        applicant_email=applicant_email,
        wait_for_processing=True
    )


if __name__ == "__main__":
    main()

