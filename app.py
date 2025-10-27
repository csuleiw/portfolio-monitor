from flask import Flask, render_template
import akshare as ak
import pandas as pd
from datetime import datetime
import traceback
import json
import concurrent.futures

app = Flask(__name__)

# 要查询的基金列表
FUNDS = [
    {"code": "518800", "name": "国泰黄金ETF"},
    {"code": "510720", "name": "招商上证消费80ETF"},
    {"code": "159781", "name": "易方达沪深300ETF"}  # 注意：1595781应该是159781
]

def get_fund_data(fund_code, start_date):
    """获取基金数据"""
    try:
        fund_df = ak.fund_etf_hist_em(symbol=fund_code, period="daily")
        return fund_df, "fund_etf_hist_em"
    except Exception as e:
        print(f"ETF接口失败: {e}")
    
    try:
        fund_df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
        return fund_df, "fund_open_fund_info_em"
    except Exception as e:
        print(f"通用接口失败: {e}")
    
    return None, None

def optimize_chart_data(dates, navs, max_points=50):
    """优化图表数据，减少数据点数量以提高性能"""
    if len(dates) <= max_points:
        return dates, navs
    
    # 等间隔采样，保持数据趋势
    step = len(dates) // max_points
    optimized_dates = dates[::step]
    optimized_navs = navs[::step]
    
    # 确保包含最新数据
    if optimized_dates[-1] != dates[-1]:
        optimized_dates.append(dates[-1])
        optimized_navs.append(navs[-1])
    
    return optimized_dates, optimized_navs

def calculate_single_fund_return(fund_info, start_date):
    """计算单只基金的涨幅数据"""
    fund_code = fund_info["code"]
    fund_name = fund_info["name"]
    
    try:
        fund_df, method_used = get_fund_data(fund_code, start_date)
        
        if fund_df is None or len(fund_df) == 0:
            return {
                'success': False,
                'code': fund_code,
                'name': fund_name,
                'error': '无法获取基金数据'
            }
        
        # 处理不同数据格式
        if '日期' in fund_df.columns and '收盘' in fund_df.columns:
            fund_df = fund_df.sort_values('日期')
            fund_df['日期'] = pd.to_datetime(fund_df['日期'])
            nav_col = '收盘'
            date_col = '日期'
        elif '净值日期' in fund_df.columns and '单位净值' in fund_df.columns:
            fund_df = fund_df.sort_values('净值日期')
            fund_df['净值日期'] = pd.to_datetime(fund_df['净值日期'])
            nav_col = '单位净值'
            date_col = '净值日期'
        else:
            return {
                'success': False,
                'code': fund_code,
                'name': fund_name,
                'error': '数据格式不支持'
            }
        
        # 过滤数据
        start_date_dt = pd.to_datetime(start_date)
        filtered_df = fund_df[fund_df[date_col] >= start_date_dt].copy()
        
        if len(filtered_df) == 0:
            return {
                'success': False,
                'code': fund_code,
                'name': fund_name,
                'error': '指定日期后无数据'
            }
        
        # 计算涨幅
        start_nav = filtered_df.iloc[0][nav_col]
        latest_nav = filtered_df.iloc[-1][nav_col]
        total_return = (latest_nav - start_nav) / start_nav * 100
        
        # 准备图表数据并优化
        dates = filtered_df[date_col].dt.strftime('%Y-%m-%d').tolist()
        navs = filtered_df[nav_col].tolist()
        
        # 优化数据点数量
        optimized_dates, optimized_navs = optimize_chart_data(dates, navs, max_points=40)
        
        chart_data = {
            'dates': optimized_dates,
            'navs': optimized_navs,
            'original_count': len(dates),
            'optimized_count': len(optimized_dates)
        }
        
        return {
            'success': True,
            'code': fund_code,
            'name': fund_name,
            'period_start': filtered_df.iloc[0][date_col].strftime('%Y-%m-%d'),
            'period_end': filtered_df.iloc[-1][date_col].strftime('%Y-%m-%d'),
            'start_nav': round(start_nav, 4),
            'latest_nav': round(latest_nav, 4),
            'total_return': round(total_return, 2),
            'trading_days': len(filtered_df),
            'chart_data': chart_data
        }
        
    except Exception as e:
        return {
            'success': False,
            'code': fund_code,
            'name': fund_name,
            'error': f'计算错误: {str(e)}'
        }

def calculate_all_funds_returns(start_date):
    """并行计算所有基金的涨幅数据"""
    results = []
    
    # 使用线程池并行获取数据
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_fund = {
            executor.submit(calculate_single_fund_return, fund_info, start_date): fund_info 
            for fund_info in FUNDS
        }
        
        for future in concurrent.futures.as_completed(future_to_fund):
            result = future.result()
            results.append(result)
    
    return results

@app.route('/')
def index():
    """显示所有基金涨幅数据"""
    start_date = "20240102"
    
    # 获取所有基金数据
    funds_data = calculate_all_funds_returns(start_date)
    current_time = datetime.now()
    
    # 将图表数据转换为JSON格式
    for fund_data in funds_data:
        if fund_data['success']:
            fund_data['chart_data_json'] = json.dumps(fund_data['chart_data'])
    
    return render_template('index.html', funds_data=funds_data, current_time=current_time)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
