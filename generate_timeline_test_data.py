"""
Comprehensive Timeline Test Data Generator
Generates large amounts of test data optimized for timeline visualization
with dates spread across different time periods
"""
import sys
import os
import random
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.db_config import DatabaseConfig
from db.db_manager import DatabaseManager
from utils.generate_test_data import (
    SOURCE_TYPES, COUNTRIES, CITIES, OWNERSHIP_TYPES, CLASSIFICATIONS,
    SOURCE_NAMES_EN, SOURCE_NAMES_AR, CONTENT_TITLES_EN, CONTENT_TITLES_AR,
    CONTENT_PARAGRAPHS_EN, CONTENT_PARAGRAPHS_AR, PEOPLE_NAMES_EN, PEOPLE_NAMES_AR,
    PLACES_EN, PLACES_AR, SIDES_EN, SIDES_AR
)


def random_date_in_range(start_date: datetime, end_date: datetime) -> datetime:
    """Generate a random date within the specified range"""
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    random_date = start_date + timedelta(days=random_days)
    # Add random time
    random_hours = random.randint(0, 23)
    random_minutes = random.randint(0, 59)
    return random_date.replace(hour=random_hours, minute=random_minutes, second=random.randint(0, 59))


def generate_timeline_source_data(index: int, date: datetime) -> dict:
    """Generate source data with specific date"""
    lang = random.choice(['en', 'ar'])
    
    if lang == 'en':
        base_name = random.choice(SOURCE_NAMES_EN)
        name = f"{base_name} {index}"
    else:
        base_name = random.choice(SOURCE_NAMES_AR)
        name = f"{base_name} {index}"
    
    country_idx = random.randint(0, len(COUNTRIES['en']) - 1)
    
    return {
        'name': name,
        'type': random.choice(SOURCE_TYPES[lang]),
        'link_sources': f"https://source{index}.example.com",
        'importance': round(random.uniform(0.2, 1.0), 2),
        'country': COUNTRIES[lang][country_idx],
        'city': CITIES[lang][country_idx % len(CITIES[lang])],
        'description': f"{'وصف المصدر رقم' if lang == 'ar' else 'Source description for'} {name}.",
        'accounts': f"@source{index}, contact@source{index}.com",
        'note': f"{'ملاحظات حول المصدر' if lang == 'ar' else 'Notes about source'} {index}",
        'ownership': random.choice(OWNERSHIP_TYPES[lang]),
        'date_entry': date,
        'date_creation': date
    }


def generate_timeline_content_data(source_id: int, index: int, date: datetime) -> dict:
    """Generate content data with specific date"""
    lang = random.choice(['en', 'ar'])
    
    title = random.choice(CONTENT_TITLES_AR if lang == 'ar' else CONTENT_TITLES_EN)
    title = f"{title} - {index}"
    
    # Generate 2-5 paragraphs of content
    num_paragraphs = random.randint(2, 5)
    paragraphs = CONTENT_PARAGRAPHS_AR if lang == 'ar' else CONTENT_PARAGRAPHS_EN
    content = "\n\n".join(random.sample(paragraphs, min(num_paragraphs, len(paragraphs))))
    
    return {
        'title': title,
        'content_data': content,
        'attachments': f"file{index}.pdf, image{index}.jpg" if random.random() > 0.5 else None,
        'note': f"{'ملاحظة المحتوى' if lang == 'ar' else 'Content note'} {index}",
        'importance': round(random.uniform(0.2, 1.0), 2),
        'date_content': date,
        'date_creation': date,
        'sources_id': source_id
    }


def generate_timeline_analysis_data(content_id: int, index: int, date: datetime) -> dict:
    """Generate analysis data with specific date"""
    lang = random.choice(['en', 'ar'])
    
    num_people = random.randint(1, 5)
    num_places = random.randint(1, 4)
    num_sides = random.randint(1, 3)
    
    people = PEOPLE_NAMES_AR if lang == 'ar' else PEOPLE_NAMES_EN
    places = PLACES_AR if lang == 'ar' else PLACES_EN
    sides = SIDES_AR if lang == 'ar' else SIDES_EN
    
    return {
        'content_id': content_id,
        'list_names_people': ", ".join(random.sample(people, min(num_people, len(people)))),
        'list_names_places': ", ".join(random.sample(places, min(num_places, len(places)))),
        'coordinates': f"{round(random.uniform(-90, 90), 6)}, {round(random.uniform(-180, 180), 6)}" if random.random() > 0.3 else None,
        'classification': random.choice(CLASSIFICATIONS[lang]),
        'list_sides': ", ".join(random.sample(sides, min(num_sides, len(sides)))),
        'date_analysis': date,
    }


def generate_comprehensive_timeline_data():
    """Generate comprehensive test data optimized for timeline visualization"""
    
    print("=" * 70)
    print("COMPREHENSIVE TIMELINE TEST DATA GENERATOR")
    print("=" * 70)
    
    # Initialize database
    print("\n[1/1] Initializing database...")
    success, error = DatabaseConfig.initialize_database()
    if not success:
        print(f"ERROR: Database initialization failed: {error}")
        return False
    
    print(f"Database path: {DatabaseConfig.get_db_path()}\n")
    
    # Define time periods for better timeline visualization
    now = datetime.now()
    periods = [
        # Recent (last 30 days) - More events
        {'start': now - timedelta(days=30), 'end': now, 'sources': 50, 'contents_per': 8, 'name': 'Recent (30 days)'},
        # Last month (30-60 days ago)
        {'start': now - timedelta(days=60), 'end': now - timedelta(days=30), 'sources': 40, 'contents_per': 6, 'name': 'Last Month'},
        # 2-3 months ago
        {'start': now - timedelta(days=90), 'end': now - timedelta(days=60), 'sources': 35, 'contents_per': 5, 'name': '2-3 Months Ago'},
        # 3-6 months ago
        {'start': now - timedelta(days=180), 'end': now - timedelta(days=90), 'sources': 30, 'contents_per': 4, 'name': '3-6 Months Ago'},
        # 6-12 months ago
        {'start': now - timedelta(days=365), 'end': now - timedelta(days=180), 'sources': 25, 'contents_per': 3, 'name': '6-12 Months Ago'},
        # Historical (1-2 years ago)
        {'start': now - timedelta(days=730), 'end': now - timedelta(days=365), 'sources': 20, 'contents_per': 2, 'name': 'Historical (1-2 years)'},
    ]
    
    total_sources = sum(p['sources'] for p in periods)
    total_contents_estimate = sum(p['sources'] * p['contents_per'] for p in periods)
    
    print(f"Generating data across {len(periods)} time periods:")
    print(f"  Total Sources: ~{total_sources}")
    print(f"  Total Contents: ~{total_contents_estimate}")
    print(f"  Estimated Analyses: ~{int(total_contents_estimate * 0.8)}\n")
    
    # Statistics
    sources_created = 0
    contents_created = 0
    analyses_created = 0
    errors = []
    
    all_source_ids = []
    all_content_ids = []
    
    # Generate data for each time period
    for period_idx, period in enumerate(periods, 1):
        print(f"\n[{period_idx}/{len(periods)}] {period['name']} ({period['start'].strftime('%Y-%m-%d')} to {period['end'].strftime('%Y-%m-%d')})")
        print(f"  Generating {period['sources']} sources...")
        
        # Generate sources for this period
        period_source_ids = []
        for i in range(period['sources']):
            try:
                source_date = random_date_in_range(period['start'], period['end'])
                source_index = sources_created + 1
                source_data = generate_timeline_source_data(source_index, source_date)
                source_id = DatabaseManager.add_source(source_data)
                period_source_ids.append(source_id)
                all_source_ids.append(source_id)
                sources_created += 1
                
                if (i + 1) % 10 == 0:
                    print(f"    Sources: {i + 1}/{period['sources']}")
                    
            except Exception as e:
                errors.append(f"Source {sources_created + 1} ({period['name']}): {str(e)}")
        
        print(f"  OK: Created {len(period_source_ids)} sources")
        
        # Generate contents for sources in this period
        print(f"  Generating contents (avg {period['contents_per']} per source)...")
        period_content_ids = []
        
        for source_id in period_source_ids:
            num_contents = random.randint(1, period['contents_per'] * 2)
            
            for j in range(num_contents):
                try:
                    content_date = random_date_in_range(period['start'], period['end'])
                    content_index = contents_created + 1
                    content_data = generate_timeline_content_data(source_id, content_index, content_date)
                    content_id = DatabaseManager.add_content(content_data)
                    period_content_ids.append(content_id)
                    all_content_ids.append(content_id)
                    contents_created += 1
                    
                except Exception as e:
                    errors.append(f"Content {contents_created + 1} ({period['name']}): {str(e)}")
        
        print(f"  OK: Created {len(period_content_ids)} contents")
        
        # Generate analyses for contents in this period
        print(f"  Generating analyses...")
        num_to_analyze = int(len(period_content_ids) * 0.8)
        contents_to_analyze = random.sample(period_content_ids, min(num_to_analyze, len(period_content_ids)))
        
        for content_id in contents_to_analyze:
            try:
                # Analysis date can be same or slightly after content date
                content_record = DatabaseManager.get_content_by_id(content_id)
                if content_record and content_record.get('date_content'):
                    content_date = content_record['date_content']
                    if isinstance(content_date, str):
                        try:
                            content_date = datetime.strptime(content_date[:19], '%Y-%m-%d %H:%M:%S')
                        except:
                            content_date = period['end']
                    analysis_date = content_date + timedelta(days=random.randint(0, 7))
                else:
                    analysis_date = random_date_in_range(period['start'], period['end'])
                
                analysis_index = analyses_created + 1
                analysis_data = generate_timeline_analysis_data(content_id, analysis_index, analysis_date)
                DatabaseManager.add_content_analysis(analysis_data)
                analyses_created += 1
                
            except Exception as e:
                errors.append(f"Analysis {analyses_created + 1} ({period['name']}): {str(e)}")
        
        print(f"  OK: Created {len(contents_to_analyze)} analyses")
    
    # Summary
    print("\n" + "=" * 70)
    print("GENERATION COMPLETE!")
    print("=" * 70)
    print(f"\nStatistics:")
    print(f"  OK: Sources created:  {sources_created:,}")
    print(f"  OK: Contents created: {contents_created:,}")
    print(f"  OK: Analyses created:  {analyses_created:,}")
    print(f"  OK: Total records:    {sources_created + contents_created + analyses_created:,}")
    
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for err in errors[:10]:
            print(f"  - {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
    else:
        print("\nNo errors!")
    
    print("\n" + "=" * 70)
    print("Timeline is now ready for testing!")
    print("Open the Timeline tab to see all events chronologically.")
    print("=" * 70 + "\n")
    
    return True


if __name__ == '__main__':
    try:
        generate_comprehensive_timeline_data()
    except KeyboardInterrupt:
        print("\n\nGeneration interrupted by user.")
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
