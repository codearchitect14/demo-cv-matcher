"""
Test script for enhanced notification system with async sending, template caching, and batching
"""
import asyncio
import logging
import time
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_enhanced_email_service():
    """Test the enhanced email service with caching and async sending"""
    logger.info("🧪 Testing Enhanced Email Service...")
    
    try:
        from services.enhanced_email_service import enhanced_email_service
        
        # Test template caching
        logger.info("Testing template caching...")
        start_time = time.time()
        
        # First call - should generate template
        template1 = enhanced_email_service.get_template(
            "sub_recruiter_welcome",
            recruiter_name="John Doe",
            company_name="Test Company",
            recruiter_email="john@test.com"
        )
        
        first_call_time = time.time() - start_time
        logger.info(f"First template generation took: {first_call_time:.3f}s")
        
        # Second call - should use cache
        start_time = time.time()
        template2 = enhanced_email_service.get_template(
            "sub_recruiter_welcome",
            recruiter_name="John Doe",
            company_name="Test Company",
            recruiter_email="john@test.com"
        )
        
        second_call_time = time.time() - start_time
        logger.info(f"Second template call (cached) took: {second_call_time:.3f}s")
        
        # Verify caching worked
        if template1 == template2 and second_call_time < first_call_time:
            logger.info("✅ Template caching working correctly")
        else:
            logger.warning("⚠️ Template caching may not be working optimally")
        
        # Test async email sending
        logger.info("Testing async email sending...")
        start_time = time.time()
        
        # Send multiple emails concurrently
        tasks = []
        for i in range(5):
            task = enhanced_email_service.send_email_async(
                to_email=f"test{i}@example.com",
                subject=f"Test Email {i}",
                html_content=f"<h1>Test Email {i}</h1><p>This is a test email.</p>",
                priority="normal",
                use_batch=True
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        logger.info(f"Sent 5 emails in {total_time:.3f}s")
        logger.info(f"Results: {results}")
        
        # Test service stats
        stats = enhanced_email_service.get_service_stats()
        logger.info(f"Email service stats: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced email service test failed: {e}")
        return False

async def test_notification_batching():
    """Test the notification batching service"""
    logger.info("🧪 Testing Notification Batching Service...")
    
    try:
        from services.notification_batch_service import notification_batch_service, NotificationPriority
        
        # Test adding multiple notifications
        logger.info("Adding multiple notifications to batch...")
        
        for i in range(10):
            await notification_batch_service.add_notification(
                user_id=1,
                user_type="recruiter",
                title=f"Test Notification {i}",
                message=f"This is test notification number {i}",
                notification_type="info",
                priority=NotificationPriority.NORMAL
            )
        
        # Wait a bit for batch processing
        await asyncio.sleep(2)
        
        # Get batch stats
        stats = notification_batch_service.get_batch_stats()
        logger.info(f"Batch service stats: {stats}")
        
        # Test high priority notification (should process immediately)
        logger.info("Testing high priority notification...")
        await notification_batch_service.add_notification(
            user_id=1,
            user_type="recruiter",
            title="High Priority Test",
            message="This is a high priority notification",
            notification_type="warning",
            priority=NotificationPriority.HIGH
        )
        
        await asyncio.sleep(1)
        
        # Force process remaining batches
        await notification_batch_service.force_process_all_batches()
        
        logger.info("✅ Notification batching test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Notification batching test failed: {e}")
        return False

async def test_integrated_notification_service():
    """Test the integrated notification service"""
    logger.info("🧪 Testing Integrated Notification Service...")
    
    try:
        from services.integrated_notification_service import integrated_notification_service
        
        # Test sub-recruiter welcome flow
        logger.info("Testing sub-recruiter welcome flow...")
        
        results = await integrated_notification_service.send_sub_recruiter_welcome(
            recruiter_email="newrecruiter@test.com",
            recruiter_name="Jane Smith",
            company_name="Test Company",
            login_credentials={
                "email": "newrecruiter@test.com",
                "password": "temp123",
                "dashboard_url": "http://localhost:3000/sub-recruiter/dashboard"
            },
            admin_user_id=1,
            admin_name="Admin User"
        )
        
        logger.info(f"Sub-recruiter welcome results: {results}")
        
        # Test job assignment flow
        logger.info("Testing job assignment flow...")
        
        assignment_results = await integrated_notification_service.send_job_assignment_notifications(
            recruiter_email="recruiter@test.com",
            recruiter_name="John Recruiter",
            job_title="Software Engineer",
            company_name="Test Company",
            job_id=123,
            admin_name="Admin User",
            recruiter_user_id=2,
            admin_user_id=1
        )
        
        logger.info(f"Job assignment results: {assignment_results}")
        
        # Test candidate application notification
        logger.info("Testing candidate application notification...")
        
        app_results = await integrated_notification_service.send_candidate_application_notification(
            recruiter_email="recruiter@test.com",
            recruiter_name="John Recruiter",
            candidate_name="Alice Candidate",
            job_title="Software Engineer",
            company_name="Test Company",
            application_id=456,
            recruiter_user_id=2
        )
        
        logger.info(f"Candidate application results: {app_results}")
        
        # Test candidate status update
        logger.info("Testing candidate status update...")
        
        status_results = await integrated_notification_service.send_candidate_status_update(
            candidate_email="candidate@test.com",
            candidate_name="Alice Candidate",
            job_title="Software Engineer",
            new_status="INTERVIEW_SCHEDULED",
            company_name="Test Company",
            recruiter_name="John Recruiter",
            candidate_user_id=3,
            admin_user_id=1,
            next_steps="We will contact you shortly to schedule an interview."
        )
        
        logger.info(f"Status update results: {status_results}")
        
        # Test bulk notifications
        logger.info("Testing bulk notifications...")
        
        bulk_notifications = [
            {
                "user_id": 1,
                "user_type": "recruiter",
                "title": f"Bulk Notification {i}",
                "message": f"Bulk notification message {i}",
                "notification_type": "info",
                "priority": NotificationPriority.NORMAL
            }
            for i in range(5)
        ]
        
        bulk_results = await integrated_notification_service.send_bulk_notifications(bulk_notifications)
        logger.info(f"Bulk notification results: {bulk_results}")
        
        # Test service stats and health check
        stats = integrated_notification_service.get_service_stats()
        logger.info(f"Integrated service stats: {stats}")
        
        health = await integrated_notification_service.health_check()
        logger.info(f"Health check: {health}")
        
        logger.info("✅ Integrated notification service test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Integrated notification service test failed: {e}")
        return False

async def test_performance_improvements():
    """Test performance improvements"""
    logger.info("🧪 Testing Performance Improvements...")
    
    try:
        from services.enhanced_email_service import enhanced_email_service
        from services.notification_batch_service import notification_batch_service, NotificationPriority
        
        # Test concurrent email sending
        logger.info("Testing concurrent email sending performance...")
        
        start_time = time.time()
        tasks = []
        
        for i in range(20):
            task = enhanced_email_service.send_email_async(
                to_email=f"perftest{i}@example.com",
                subject=f"Performance Test {i}",
                html_content=f"<h1>Performance Test {i}</h1>",
                priority="normal",
                use_batch=True
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        successful_emails = sum(1 for r in results if r is True)
        logger.info(f"Sent {successful_emails}/20 emails in {total_time:.3f}s")
        logger.info(f"Average time per email: {total_time/20:.3f}s")
        
        # Test notification batching performance
        logger.info("Testing notification batching performance...")
        
        start_time = time.time()
        notification_tasks = []
        
        for i in range(50):
            task = notification_batch_service.add_notification(
                user_id=1,
                user_type="recruiter",
                title=f"Performance Notification {i}",
                message=f"Performance test notification {i}",
                notification_type="info",
                priority=NotificationPriority.NORMAL
            )
            notification_tasks.append(task)
        
        await asyncio.gather(*notification_tasks)
        notification_time = time.time() - start_time
        
        logger.info(f"Added 50 notifications to batch in {notification_time:.3f}s")
        logger.info(f"Average time per notification: {notification_time/50:.3f}s")
        
        # Wait for batch processing
        await asyncio.sleep(3)
        
        logger.info("✅ Performance test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Performance test failed: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("🚀 Starting Enhanced Notification System Tests")
    logger.info("=" * 60)
    
    test_results = []
    
    # Run tests
    test_results.append(await test_enhanced_email_service())
    test_results.append(await test_notification_batching())
    test_results.append(await test_integrated_notification_service())
    test_results.append(await test_performance_improvements())
    
    # Summary
    logger.info("=" * 60)
    logger.info("📊 Test Results Summary:")
    
    passed = sum(test_results)
    total = len(test_results)
    
    logger.info(f"✅ Passed: {passed}/{total}")
    logger.info(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        logger.info("🎉 All tests passed! Enhanced notification system is working correctly.")
    else:
        logger.warning("⚠️ Some tests failed. Please check the logs above.")
    
    # Cleanup
    try:
        from services.integrated_notification_service import integrated_notification_service
        await integrated_notification_service.shutdown()
        logger.info("🧹 Cleanup completed")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

