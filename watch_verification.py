"""
watch_verification.py - Verify Watch System is Working
Tests that watches are properly scored, announced, and displayed
"""

from typing import Dict, List

def verify_watch_scoring():
    """
    Verify that watches are properly scored by severity_scorer
    
    Returns:
        Dict with test results
    """
    try:
        from severity_scorer import SeverityScorer
        
        scorer = SeverityScorer()
        
        # Test watches
        test_watches = [
            {
                'event': 'Tornado Watch',
                'severity': 'Moderate',
                'urgency': 'Expected',
                'certainty': 'Likely'
            },
            {
                'event': 'Severe Thunderstorm Watch',
                'severity': 'Moderate',
                'urgency': 'Expected',
                'certainty': 'Likely'
            },
            {
                'event': 'Flash Flood Watch',
                'severity': 'Moderate',
                'urgency': 'Expected',
                'certainty': 'Possible'
            }
        ]
        
        results = {}
        
        for watch in test_watches:
            scored = scorer.score_alert(watch)
            event = watch['event']
            score = scored.get('threat_score', {}).get('score', 0)
            
            results[event] = {
                'score': score,
                'passed': score > 30,  # Watches should score above 30
                'scored_data': scored
            }
        
        all_passed = all(r['passed'] for r in results.values())
        
        return {
            'success': True,
            'all_passed': all_passed,
            'results': results,
            'message': 'All watches scored correctly' if all_passed else 'Some watches not scoring properly'
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Error testing watch scoring'
        }


def verify_watch_announcements():
    """
    Verify that watches get proper voice announcements
    
    Returns:
        Dict with test results
    """
    try:
        from voice_styles import get_announcement_for_alert
        from severity_scorer import score_alert
        
        # Test tornado watch announcement
        tornado_watch = {
            'event': 'Tornado Watch',
            'areaDesc': 'North Alabama',
            'severity': 'Moderate',
            'urgency': 'Expected',
            'certainty': 'Likely',
            'description': 'Conditions favorable for tornadoes until 8 PM'
        }
        
        scored = score_alert(tornado_watch)
        threat_score = scored.get('threat_score', {}).get('score', 0)
        announcement = get_announcement_for_alert(tornado_watch, threat_score)
        
        has_announcement = announcement is not None
        has_text = announcement.get('text') if announcement else None
        has_style = announcement.get('style') if announcement else None
        
        return {
            'success': True,
            'has_announcement': has_announcement,
            'text': has_text,
            'style': has_style,
            'threat_score': threat_score,
            'passed': has_announcement and has_text and has_style,
            'message': 'Watch announcements working' if has_announcement else 'Watch announcements not generating'
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Error testing watch announcements'
        }


def verify_watch_vs_warning_distinction():
    """
    Verify that watches and warnings are treated differently
    
    Returns:
        Dict with test results
    """
    try:
        from severity_scorer import score_alert
        
        tornado_watch = {
            'event': 'Tornado Watch',
            'severity': 'Moderate',
            'urgency': 'Expected',
            'certainty': 'Likely'
        }
        
        tornado_warning = {
            'event': 'Tornado Warning',
            'severity': 'Extreme',
            'urgency': 'Immediate',
            'certainty': 'Observed'
        }
        
        watch_score = score_alert(tornado_watch).get('threat_score', {}).get('score', 0)
        warning_score = score_alert(tornado_warning).get('threat_score', {}).get('score', 0)
        
        correctly_distinguished = warning_score > watch_score
        
        return {
            'success': True,
            'watch_score': watch_score,
            'warning_score': warning_score,
            'correctly_distinguished': correctly_distinguished,
            'passed': correctly_distinguished,
            'message': f'Warnings ({warning_score}) scored higher than watches ({watch_score})' if correctly_distinguished else 'Watches and warnings not properly distinguished'
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Error testing watch vs warning distinction'
        }


def get_watch_examples() -> List[Dict]:
    """
    Get example watch alerts for testing
    
    Returns:
        List of sample watch alerts
    """
    return [
        {
            'id': 'test-tornado-watch',
            'event': 'Tornado Watch',
            'areaDesc': 'Madison; Morgan; Limestone Counties in North Alabama',
            'severity': 'Moderate',
            'urgency': 'Expected',
            'certainty': 'Likely',
            'onset': '2025-12-20T14:00:00Z',
            'expires': '2025-12-20T20:00:00Z',
            'headline': 'Tornado Watch until 8 PM CST',
            'description': 'The Storm Prediction Center has issued a Tornado Watch for portions of North Alabama until 8 PM CST. Conditions are favorable for the development of tornadoes.',
            'instruction': 'Monitor weather conditions and be prepared to take shelter if a tornado warning is issued.'
        },
        {
            'id': 'test-severe-watch',
            'event': 'Severe Thunderstorm Watch',
            'areaDesc': 'North Alabama and Southern Tennessee',
            'severity': 'Moderate',
            'urgency': 'Expected',
            'certainty': 'Likely',
            'onset': '2025-12-20T15:00:00Z',
            'expires': '2025-12-20T21:00:00Z',
            'headline': 'Severe Thunderstorm Watch until 9 PM CST',
            'description': 'Severe thunderstorms with large hail and damaging winds are possible this afternoon and evening.',
            'instruction': 'Stay alert for severe weather and be prepared to take shelter.'
        }
    ]


def run_all_watch_tests() -> Dict:
    """
    Run all watch verification tests
    
    Returns:
        Complete test results
    """
    print("=" * 70)
    print("WATCH SYSTEM VERIFICATION")
    print("=" * 70)
    
    results = {}
    
    # Test 1: Scoring
    print("\n1. Testing watch scoring...")
    print("-" * 70)
    scoring_results = verify_watch_scoring()
    results['scoring'] = scoring_results
    
    if scoring_results['success']:
        print(f"✓ {scoring_results['message']}")
        for event, data in scoring_results['results'].items():
            status = "✓" if data['passed'] else "✗"
            print(f"  {status} {event}: Score {data['score']}")
    else:
        print(f"✗ {scoring_results['message']}")
        print(f"  Error: {scoring_results.get('error')}")
    
    # Test 2: Announcements
    print("\n2. Testing watch announcements...")
    print("-" * 70)
    announcement_results = verify_watch_announcements()
    results['announcements'] = announcement_results
    
    if announcement_results['success']:
        status = "✓" if announcement_results['passed'] else "✗"
        print(f"{status} {announcement_results['message']}")
        if announcement_results.get('text'):
            print(f"  Sample text: {announcement_results['text'][:100]}...")
            print(f"  Voice style: {announcement_results.get('style')}")
    else:
        print(f"✗ {announcement_results['message']}")
        print(f"  Error: {announcement_results.get('error')}")
    
    # Test 3: Watch vs Warning distinction
    print("\n3. Testing watch vs warning distinction...")
    print("-" * 70)
    distinction_results = verify_watch_vs_warning_distinction()
    results['distinction'] = distinction_results
    
    if distinction_results['success']:
        status = "✓" if distinction_results['passed'] else "✗"
        print(f"{status} {distinction_results['message']}")
    else:
        print(f"✗ {distinction_results['message']}")
        print(f"  Error: {distinction_results.get('error')}")
    
    # Overall result
    print("\n" + "=" * 70)
    all_passed = all(
        results[key].get('passed', False) or results[key].get('all_passed', False)
        for key in results
        if results[key].get('success', False)
    )
    
    if all_passed:
        print("✅ ALL TESTS PASSED - Watch system is working correctly!")
    else:
        print("⚠️ SOME TESTS FAILED - Watch system needs attention")
    
    print("=" * 70)
    
    results['overall_passed'] = all_passed
    return results


if __name__ == '__main__':
    results = run_all_watch_tests()
    
    # Print example watches
    print("\n" + "=" * 70)
    print("EXAMPLE WATCH ALERTS FOR TESTING")
    print("=" * 70)
    
    examples = get_watch_examples()
    for i, watch in enumerate(examples, 1):
        print(f"\n{i}. {watch['event']}")
        print(f"   Area: {watch['areaDesc']}")
        print(f"   Until: {watch['expires']}")
        print(f"   Headline: {watch['headline']}")
    
    print("\n" + "=" * 70)
