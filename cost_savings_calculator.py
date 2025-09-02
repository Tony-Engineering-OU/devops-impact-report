import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

class DevOpsCostSavingsCalculator:
    def __init__(self):
        # Business assumptions adjusted for very small project scale
        # Based on EC2 costs ~$1K/month peak, this is a small team/project
        self.dev_hourly_rate = 25  # USD per hour (but limited time impact)
        self.avg_team_size = 2  # Very small team based on deployment volume
        
        # Incident costs (scaled down significantly)
        self.incident_resolution_hours = 1  # Quick fixes for small project
        self.incident_stakeholder_hours = 0.5  # Minimal stakeholder involvement
        self.stakeholder_hourly_rate = 75  # USD per hour
        
        # Opportunity costs (very conservative for small project)
        self.revenue_per_feature_per_day = 10  # Small project revenue impact
        self.manual_testing_hours_saved = 2  # Realistic testing time saved
        
        # No projection factors - use simple calculation
        
    def load_current_data(self):
        """Load existing dashboard data"""
        # Read deployment data
        df = pd.read_csv('deploy_prod_pipelines_2022_2025_argocd_refined.csv')
        df['branch_creation_datetime'] = pd.to_datetime(df['branch_creation_datetime'], utc=True, format='mixed')
        
        # Read EC2 costs
        ec2_df = pd.read_csv('ec2_costs_us_east_1.csv')
        ec2_df['commit_date'] = pd.to_datetime(ec2_df['commit_date'])
        
        return df, ec2_df
    
    def calculate_monthly_savings(self, df, ec2_df):
        """Calculate monthly cost savings components"""
        autodeploy_date = pd.to_datetime('2023-12-12T14:13:04.057Z')
        
        # Calculate monthly metrics
        df['year_month'] = df['branch_creation_datetime'].dt.to_period('M')
        monthly_stats = df.groupby('year_month').apply(lambda x: pd.Series({
            'total_deployments': len(x),
            'successful_deployments': len(x[x['deploy_prod_job_end_datetime'].notna()]),
            'avg_deployment_days': x[x['days_elapsed_branch_to_deploy'] > 0]['days_elapsed_branch_to_deploy'].mean() if len(x[x['days_elapsed_branch_to_deploy'] > 0]) > 0 else 0,
            'failure_rate': 1 - (len(x[x['deploy_prod_job_end_datetime'].notna()]) / len(x)) if len(x) > 0 else 0,
            'is_post_autodeploy': x['branch_creation_datetime'].iloc[0] >= autodeploy_date
        })).reset_index()
        
        # Calculate savings for each month
        savings_data = []
        
        # Baseline metrics (pre-autodeploy averages) - realistic for small project
        baseline_avg_days = 6.5
        baseline_failure_rate = 0.941
        baseline_deployments_per_month = 25  # More realistic for small team
        
        for _, row in monthly_stats.iterrows():
            month = row['year_month']
            is_post = row['is_post_autodeploy']
            
            if is_post:
                # Calculate time savings (much more conservative)
                time_saved_days = max(0, baseline_avg_days - row['avg_deployment_days'])
                # Small project: developers don't spend full days waiting for deployments
                time_savings_per_deployment = time_saved_days * 2 * self.dev_hourly_rate  # Only 2 hours per day actually saved
                monthly_time_savings = time_savings_per_deployment * row['total_deployments'] * 0.3  # Only 30% of deployments have significant time impact
                
                # Calculate failure cost savings  
                baseline_failures = baseline_deployments_per_month * baseline_failure_rate
                actual_failures = row['total_deployments'] * row['failure_rate']
                failures_avoided = max(0, baseline_failures - actual_failures)
                
                failure_cost_per_incident = (
                    self.incident_resolution_hours * self.dev_hourly_rate +
                    self.incident_stakeholder_hours * self.stakeholder_hourly_rate
                )
                monthly_failure_savings = failures_avoided * failure_cost_per_incident
                
                # Manual testing savings (very conservative for small project)
                manual_testing_savings = (
                    row['total_deployments'] * 
                    self.manual_testing_hours_saved * 
                    self.dev_hourly_rate * 0.2  # Only 20% reduction in manual testing
                )
                
                # Opportunity cost savings (minimal for small project)
                opportunity_savings = (
                    time_saved_days * 
                    row['total_deployments'] * 
                    self.revenue_per_feature_per_day * 0.1  # Only 10% of features generate revenue
                )
                
                total_monthly_savings = (
                    monthly_time_savings + 
                    monthly_failure_savings + 
                    manual_testing_savings + 
                    opportunity_savings
                )
            else:
                total_monthly_savings = 0
            
            # Get EC2 costs for the month
            month_str = str(month)
            ec2_month_costs = 0
            ec2_monthly = ec2_df[ec2_df['commit_date'].dt.to_period('M') == month]
            if not ec2_monthly.empty:
                ec2_month_costs = ec2_monthly['ec2_cost_usd'].iloc[-1]  # Take latest value
            
            savings_data.append({
                'month': month_str,
                'total_savings': total_monthly_savings,
                'time_savings': monthly_time_savings if is_post else 0,
                'failure_savings': monthly_failure_savings if is_post else 0,
                'testing_savings': manual_testing_savings if is_post else 0,
                'opportunity_savings': opportunity_savings if is_post else 0,
                'ec2_costs': ec2_month_costs,
                'net_savings': total_monthly_savings - ec2_month_costs if is_post else 0,
                'is_post_autodeploy': is_post,
                'deployments': row['total_deployments'],
                'avg_deployment_days': row['avg_deployment_days']
            })
        
        return pd.DataFrame(savings_data)
    
    # Removed projections - only using historical actual data
    
    def calculate_total_savings(self):
        """Calculate and return only historical actual savings"""
        # Load data and calculate savings
        df, ec2_df = self.load_current_data()
        historical_savings = self.calculate_monthly_savings(df, ec2_df)
        
        # Historical actual savings (2024-2025 observed)
        historical_actual = historical_savings[historical_savings['is_post_autodeploy']]['net_savings'].sum()
        
        results = {
            'historical_actual_savings_2024_2025': historical_actual,
            'historical_df': historical_savings,
            'key_metrics': {
                'avg_monthly_savings_current': historical_savings[historical_savings['is_post_autodeploy']]['net_savings'].mean(),
                'deployment_time_reduction_days': 6.5 - 2.8,
                'failure_rate_reduction': 94.1 - 9.4,
                'completion_rate_improvement': 90.6 - 5.9
            }
        }
        
        return results

def create_cost_savings_report():
    """Generate historical cost savings report"""
    calculator = DevOpsCostSavingsCalculator()
    results = calculator.calculate_total_savings()
    
    print("💰 DEVOPS COST SAVINGS ANALYSIS (HISTORICAL ACTUAL)")
    print("=" * 60)
    print(f"📊 Historical Actual Savings (2024-2025): ${results['historical_actual_savings_2024_2025']:,.2f}")
    print()
    
    print("📋 KEY IMPROVEMENT METRICS:")
    metrics = results['key_metrics']
    print(f"   • Deployment time reduced by: {metrics['deployment_time_reduction_days']:.1f} days")
    print(f"   • Failure rate reduced by: {metrics['failure_rate_reduction']:.1f} percentage points")  
    print(f"   • Completion rate improved by: {metrics['completion_rate_improvement']:.1f} percentage points")
    print(f"   • Average monthly savings: ${metrics['avg_monthly_savings_current']:,.2f}")
    print()
    
    # Save detailed data
    results['historical_df'].to_csv('historical_monthly_savings.csv', index=False)
    
    # Save summary JSON
    summary = {
        'historical_actual_savings_usd': float(results['historical_actual_savings_2024_2025']),
        'calculation_date': datetime.now().isoformat(),
        'methodology': 'Developer time savings + failure cost reduction + testing efficiency + opportunity costs',
        'period': 'Historical actual data from 2024-2025 post-autodeploy implementation',
        'key_assumptions': {
            'dev_hourly_rate_usd': calculator.dev_hourly_rate,
            'team_size': calculator.avg_team_size
        }
    }
    
    with open('cost_savings_summary.json', 'w') as f:
        json.dump(summary, f, indent=4)
    
    print("✅ Reports generated:")
    print("   • historical_monthly_savings.csv")
    print("   • cost_savings_summary.json")
    
    return results

if __name__ == "__main__":
    results = create_cost_savings_report()
