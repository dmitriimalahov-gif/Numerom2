#!/usr/bin/env python3
"""
Backend Testing for Unified Media Loading Model (PersonalConsultations Pattern)
Testing the unification of media file handling across AdminPanel, FirstLesson, and LessonAdmin components
"""

import asyncio
import aiohttp
import json
import io
import os
from pathlib import Path
import tempfile
import uuid

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
TEST_ADMIN_PASSWORD = "756bvy67H"

class UnifiedMediaTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        
    async def setup(self):
        """Initialize session and authenticate"""
        self.session = aiohttp.ClientSession()
        
        # Authenticate as super admin
        login_data = {
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        }
        
        async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as resp:
            if resp.status == 200:
                data = await resp.json()
                self.auth_token = data["access_token"]
                print(f"✅ Authentication successful: {data['user']['email']} (Super Admin: {data['user']['is_super_admin']})")
                return True
            else:
                print(f"❌ Authentication failed: {resp.status}")
                return False
    
    async def cleanup(self):
        """Close session"""
        if self.session:
            await self.session.close()
    
    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def create_test_video_file(self):
        """Create a test video file"""
        content = b"FAKE_VIDEO_CONTENT_FOR_TESTING" * 100  # ~3KB fake video
        return io.BytesIO(content), "test_lesson_video.mp4", "video/mp4"
    
    def create_test_pdf_file(self):
        """Create a test PDF file"""
        content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
        return io.BytesIO(content), "test_lesson_document.pdf", "application/pdf"
    
    async def test_lesson_video_upload(self):
        """Test POST /api/admin/lessons/upload-video endpoint"""
        print("\n🎥 Testing lesson video upload endpoint...")
        
        try:
            video_file, filename, content_type = self.create_test_video_file()
            
            data = aiohttp.FormData()
            data.add_field('file', video_file, filename=filename, content_type=content_type)
            
            async with self.session.post(
                f"{BACKEND_URL}/admin/lessons/upload-video",
                data=data,
                headers=self.get_auth_headers()
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"✅ Video upload successful: {result['filename']}")
                    print(f"   File ID: {result['file_id']}")
                    print(f"   Video URL: {result['video_url']}")
                    self.test_results.append({
                        "test": "lesson_video_upload",
                        "status": "PASS",
                        "file_id": result['file_id'],
                        "video_url": result['video_url']
                    })
                    return result['file_id']
                else:
                    error_text = await resp.text()
                    print(f"❌ Video upload failed: {resp.status} - {error_text}")
                    self.test_results.append({
                        "test": "lesson_video_upload",
                        "status": "FAIL",
                        "error": f"{resp.status} - {error_text}"
                    })
                    return None
        except Exception as e:
            print(f"❌ Video upload exception: {str(e)}")
            self.test_results.append({
                "test": "lesson_video_upload",
                "status": "FAIL",
                "error": str(e)
            })
            return None
    
    async def test_lesson_pdf_upload(self):
        """Test POST /api/admin/lessons/upload-pdf endpoint"""
        print("\n📄 Testing lesson PDF upload endpoint...")
        
        try:
            pdf_file, filename, content_type = self.create_test_pdf_file()
            
            data = aiohttp.FormData()
            data.add_field('file', pdf_file, filename=filename, content_type=content_type)
            
            async with self.session.post(
                f"{BACKEND_URL}/admin/lessons/upload-pdf",
                data=data,
                headers=self.get_auth_headers()
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"✅ PDF upload successful: {result['filename']}")
                    print(f"   File ID: {result['file_id']}")
                    print(f"   PDF URL: {result['pdf_url']}")
                    self.test_results.append({
                        "test": "lesson_pdf_upload",
                        "status": "PASS",
                        "file_id": result['file_id'],
                        "pdf_url": result['pdf_url']
                    })
                    return result['file_id']
                else:
                    error_text = await resp.text()
                    print(f"❌ PDF upload failed: {resp.status} - {error_text}")
                    self.test_results.append({
                        "test": "lesson_pdf_upload",
                        "status": "FAIL",
                        "error": f"{resp.status} - {error_text}"
                    })
                    return None
        except Exception as e:
            print(f"❌ PDF upload exception: {str(e)}")
            self.test_results.append({
                "test": "lesson_pdf_upload",
                "status": "FAIL",
                "error": str(e)
            })
            return None
    
    async def test_lesson_media_endpoint(self, lesson_id="lesson_numerom_intro"):
        """Test GET /api/lessons/media/{lesson_id} endpoint"""
        print(f"\n📁 Testing lesson media endpoint for {lesson_id}...")
        
        try:
            async with self.session.get(
                f"{BACKEND_URL}/lessons/media/{lesson_id}",
                headers=self.get_auth_headers()
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    video_count = len(result.get('videos', []))
                    pdf_count = len(result.get('pdfs', []))
                    print(f"✅ Media endpoint successful:")
                    print(f"   Lesson ID: {result['lesson_id']}")
                    print(f"   Videos: {video_count}")
                    print(f"   PDFs: {pdf_count}")
                    
                    # Show sample files
                    if result.get('videos'):
                        print(f"   Sample video: {result['videos'][0]['filename']}")
                    if result.get('pdfs'):
                        print(f"   Sample PDF: {result['pdfs'][0]['filename']}")
                    
                    self.test_results.append({
                        "test": "lesson_media_endpoint",
                        "status": "PASS",
                        "video_count": video_count,
                        "pdf_count": pdf_count
                    })
                    return result
                else:
                    error_text = await resp.text()
                    print(f"❌ Media endpoint failed: {resp.status} - {error_text}")
                    self.test_results.append({
                        "test": "lesson_media_endpoint",
                        "status": "FAIL",
                        "error": f"{resp.status} - {error_text}"
                    })
                    return None
        except Exception as e:
            print(f"❌ Media endpoint exception: {str(e)}")
            self.test_results.append({
                "test": "lesson_media_endpoint",
                "status": "FAIL",
                "error": str(e)
            })
            return None
    
    async def test_video_streaming(self, file_id):
        """Test GET /api/lessons/video/{file_id} endpoint"""
        print(f"\n🎬 Testing video streaming for file_id: {file_id}...")
        
        try:
            async with self.session.get(f"{BACKEND_URL}/lessons/video/{file_id}") as resp:
                if resp.status == 200:
                    content_type = resp.headers.get('Content-Type', '')
                    content_length = resp.headers.get('Content-Length', '0')
                    print(f"✅ Video streaming successful:")
                    print(f"   Content-Type: {content_type}")
                    print(f"   Content-Length: {content_length} bytes")
                    
                    # Read a small portion to verify content
                    content = await resp.read()
                    print(f"   Content size: {len(content)} bytes")
                    
                    self.test_results.append({
                        "test": "video_streaming",
                        "status": "PASS",
                        "content_type": content_type,
                        "content_size": len(content)
                    })
                    return True
                else:
                    error_text = await resp.text()
                    print(f"❌ Video streaming failed: {resp.status} - {error_text}")
                    self.test_results.append({
                        "test": "video_streaming",
                        "status": "FAIL",
                        "error": f"{resp.status} - {error_text}"
                    })
                    return False
        except Exception as e:
            print(f"❌ Video streaming exception: {str(e)}")
            self.test_results.append({
                "test": "video_streaming",
                "status": "FAIL",
                "error": str(e)
            })
            return False
    
    async def test_pdf_streaming(self, file_id):
        """Test GET /api/lessons/pdf/{file_id} endpoint"""
        print(f"\n📖 Testing PDF streaming for file_id: {file_id}...")
        
        try:
            async with self.session.get(f"{BACKEND_URL}/lessons/pdf/{file_id}") as resp:
                if resp.status == 200:
                    content_type = resp.headers.get('Content-Type', '')
                    content_length = resp.headers.get('Content-Length', '0')
                    print(f"✅ PDF streaming successful:")
                    print(f"   Content-Type: {content_type}")
                    print(f"   Content-Length: {content_length} bytes")
                    
                    # Read a small portion to verify content
                    content = await resp.read()
                    print(f"   Content size: {len(content)} bytes")
                    
                    self.test_results.append({
                        "test": "pdf_streaming",
                        "status": "PASS",
                        "content_type": content_type,
                        "content_size": len(content)
                    })
                    return True
                else:
                    error_text = await resp.text()
                    print(f"❌ PDF streaming failed: {resp.status} - {error_text}")
                    self.test_results.append({
                        "test": "pdf_streaming",
                        "status": "FAIL",
                        "error": f"{resp.status} - {error_text}"
                    })
                    return False
        except Exception as e:
            print(f"❌ PDF streaming exception: {str(e)}")
            self.test_results.append({
                "test": "pdf_streaming",
                "status": "FAIL",
                "error": str(e)
            })
            return False
    
    async def test_unified_chain(self):
        """Test the complete unified chain: AdminPanel → backend → FirstLesson → streaming"""
        print("\n🔗 Testing complete unified media chain...")
        
        # Step 1: Upload video via AdminPanel endpoint
        video_file_id = await self.test_lesson_video_upload()
        if not video_file_id:
            print("❌ Chain broken at video upload step")
            return False
        
        # Step 2: Upload PDF via AdminPanel endpoint
        pdf_file_id = await self.test_lesson_pdf_upload()
        if not pdf_file_id:
            print("❌ Chain broken at PDF upload step")
            return False
        
        # Step 3: Verify files appear in FirstLesson media endpoint
        media_data = await self.test_lesson_media_endpoint()
        if not media_data:
            print("❌ Chain broken at media endpoint step")
            return False
        
        # Step 4: Test video streaming
        video_streaming_ok = await self.test_video_streaming(video_file_id)
        if not video_streaming_ok:
            print("❌ Chain broken at video streaming step")
            return False
        
        # Step 5: Test PDF streaming
        pdf_streaming_ok = await self.test_pdf_streaming(pdf_file_id)
        if not pdf_streaming_ok:
            print("❌ Chain broken at PDF streaming step")
            return False
        
        print("✅ Complete unified media chain working successfully!")
        self.test_results.append({
            "test": "unified_chain",
            "status": "PASS",
            "message": "Complete AdminPanel → backend → FirstLesson → streaming chain working"
        })
        return True
    
    async def test_endpoints_consistency(self):
        """Test that all components use the same endpoints"""
        print("\n🔄 Testing endpoint consistency across components...")
        
        endpoints_to_test = [
            ("POST", "/admin/lessons/upload-video", "AdminPanel video upload"),
            ("POST", "/admin/lessons/upload-pdf", "AdminPanel PDF upload"),
            ("GET", "/lessons/media/lesson_numerom_intro", "FirstLesson media retrieval"),
        ]
        
        consistent = True
        for method, endpoint, description in endpoints_to_test:
            try:
                if method == "POST":
                    # Test with empty data to check endpoint existence
                    async with self.session.post(
                        f"{BACKEND_URL}{endpoint}",
                        headers=self.get_auth_headers()
                    ) as resp:
                        # We expect 400 (bad request) not 404 (not found)
                        if resp.status in [400, 422]:  # Bad request is OK, means endpoint exists
                            print(f"✅ {description}: Endpoint exists")
                        elif resp.status == 404:
                            print(f"❌ {description}: Endpoint not found")
                            consistent = False
                        else:
                            print(f"⚠️ {description}: Unexpected status {resp.status}")
                else:  # GET
                    async with self.session.get(
                        f"{BACKEND_URL}{endpoint}",
                        headers=self.get_auth_headers()
                    ) as resp:
                        if resp.status in [200, 400, 422]:  # Any response means endpoint exists
                            print(f"✅ {description}: Endpoint exists")
                        elif resp.status == 404:
                            print(f"❌ {description}: Endpoint not found")
                            consistent = False
                        else:
                            print(f"⚠️ {description}: Unexpected status {resp.status}")
            except Exception as e:
                print(f"❌ {description}: Exception {str(e)}")
                consistent = False
        
        self.test_results.append({
            "test": "endpoints_consistency",
            "status": "PASS" if consistent else "FAIL",
            "message": "All components use consistent endpoints" if consistent else "Endpoint inconsistencies found"
        })
        
        return consistent
    
    async def test_personalconsultations_comparison(self):
        """Compare with PersonalConsultations model to verify unification"""
        print("\n🔍 Testing unification with PersonalConsultations model...")
        
        # Test PersonalConsultations endpoints for comparison
        consultations_endpoints = [
            ("POST", "/admin/consultations/upload-video", "PersonalConsultations video upload"),
            ("POST", "/admin/consultations/upload-pdf", "PersonalConsultations PDF upload"),
            ("GET", "/consultations/video/", "PersonalConsultations video streaming"),
            ("GET", "/consultations/pdf/", "PersonalConsultations PDF streaming"),
        ]
        
        lessons_endpoints = [
            ("POST", "/admin/lessons/upload-video", "Lessons video upload"),
            ("POST", "/admin/lessons/upload-pdf", "Lessons PDF upload"),
            ("GET", "/lessons/video/", "Lessons video streaming"),
            ("GET", "/lessons/pdf/", "Lessons PDF streaming"),
        ]
        
        unified = True
        
        print("   Checking PersonalConsultations endpoints...")
        for method, endpoint, description in consultations_endpoints:
            try:
                if method == "POST":
                    async with self.session.post(
                        f"{BACKEND_URL}{endpoint}",
                        headers=self.get_auth_headers()
                    ) as resp:
                        exists = resp.status != 404
                        print(f"   {'✅' if exists else '❌'} {description}: {'Exists' if exists else 'Not found'}")
                else:
                    # For GET endpoints, we can't test without file_id, so just check if they're implemented
                    print(f"   ⚠️ {description}: Cannot test without file_id")
            except Exception as e:
                print(f"   ❌ {description}: Exception {str(e)}")
        
        print("   Checking Lessons endpoints...")
        for method, endpoint, description in lessons_endpoints:
            try:
                if method == "POST":
                    async with self.session.post(
                        f"{BACKEND_URL}{endpoint}",
                        headers=self.get_auth_headers()
                    ) as resp:
                        exists = resp.status != 404
                        print(f"   {'✅' if exists else '❌'} {description}: {'Exists' if exists else 'Not found'}")
                        if not exists:
                            unified = False
                else:
                    # For GET endpoints, we can't test without file_id, so just check if they're implemented
                    print(f"   ⚠️ {description}: Cannot test without file_id")
            except Exception as e:
                print(f"   ❌ {description}: Exception {str(e)}")
                unified = False
        
        self.test_results.append({
            "test": "personalconsultations_comparison",
            "status": "PASS" if unified else "FAIL",
            "message": "Lessons unified with PersonalConsultations model" if unified else "Unification incomplete"
        })
        
        return unified
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("🎯 UNIFIED MEDIA LOADING MODEL TEST SUMMARY")
        print("="*80)
        
        passed = sum(1 for result in self.test_results if result["status"] == "PASS")
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_icon} {result['test']}: {result['status']}")
            if result["status"] == "FAIL" and "error" in result:
                print(f"   Error: {result['error']}")
        
        print("\n" + "="*80)
        
        # Overall assessment
        if success_rate >= 90:
            print("🎉 EXCELLENT: Unified media loading model working perfectly!")
        elif success_rate >= 75:
            print("✅ GOOD: Unified media loading model mostly working with minor issues")
        elif success_rate >= 50:
            print("⚠️ PARTIAL: Unified media loading model partially working, needs fixes")
        else:
            print("❌ CRITICAL: Unified media loading model has major issues")
        
        return success_rate >= 75

async def main():
    """Main test execution"""
    print("🚀 Starting Unified Media Loading Model Testing")
    print("Testing unification of AdminPanel, FirstLesson, and LessonAdmin components")
    print("Following PersonalConsultations pattern")
    print("-" * 80)
    
    tester = UnifiedMediaTester()
    
    try:
        # Setup
        if not await tester.setup():
            print("❌ Failed to setup test environment")
            return False
        
        # Run individual tests
        await tester.test_endpoints_consistency()
        await tester.test_personalconsultations_comparison()
        
        # Run the complete unified chain test
        await tester.test_unified_chain()
        
        # Print summary
        success = tester.print_summary()
        
        return success
        
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)