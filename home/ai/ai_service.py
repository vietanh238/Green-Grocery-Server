import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
import joblib
import os
from django.conf import settings


class DemandForecastAI:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = os.path.join(
            settings.BASE_DIR, 'ai_models', 'demand_forecast.pkl')
        self.scaler_path = os.path.join(
            settings.BASE_DIR, 'ai_models', 'scaler.pkl')
        self.product_stats = {}

        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

        self.load_model()

    def prepare_training_data(self, sales_history):
        if not sales_history:
            return None, None

        df = pd.DataFrame(sales_history)
        df['date'] = pd.to_datetime(df['created_at'])

        daily_sales = df.groupby(['product_id', df['date'].dt.date]).agg({
            'quantity': 'sum',
            'total_amount': 'sum'
        }).reset_index()

        daily_sales.columns = ['product_id', 'date', 'quantity', 'revenue']
        daily_sales['date'] = pd.to_datetime(daily_sales['date'])

        features_list = []
        targets_list = []

        for product_id in daily_sales['product_id'].unique():
            product_data = daily_sales[daily_sales['product_id'] == product_id].sort_values(
                'date')

            # Giảm requirement xuống chỉ cần 1 ngày dữ liệu
            if len(product_data) < 1:
                continue

            product_data = product_data.set_index('date')
            product_data = product_data.asfreq('D', fill_value=0)

            # Với ít data, dùng lookback linh hoạt
            total_days = len(product_data)

            # Nếu chỉ có 1-2 ngày, tạo 1 sample đơn giản
            if total_days <= 2:
                if total_days >= 1:
                    features = self._extract_features_minimal(product_data, total_days - 1)
                    # Target là quantity của ngày cuối (dự đoán ngày tiếp theo giống ngày này)
                    target = product_data.iloc[-1]['quantity']
                    features_list.append(features)
                    targets_list.append(target)
            else:
                # Với 3+ ngày, dùng phương pháp time series
                lookback = min(2, total_days - 1)
                forecast_days = 1

                for i in range(lookback, total_days - forecast_days):
                    features = self._extract_features_simple(product_data, i, lookback)
                    target = product_data.iloc[i + forecast_days]['quantity']
                    features_list.append(features)
                    targets_list.append(target)

        if not features_list:
            return None, None

        X = np.array(features_list)
        y = np.array(targets_list)

        return X, y

    def _extract_features(self, product_data, current_idx):
        """Legacy feature extraction for 7-day lookback"""
        features = []

        last_7_days = product_data.iloc[current_idx -
                                        7:current_idx]['quantity'].values
        features.extend(last_7_days)

        features.append(
            product_data.iloc[current_idx-7:current_idx]['quantity'].mean())
        features.append(
            product_data.iloc[current_idx-7:current_idx]['quantity'].std())
        features.append(
            product_data.iloc[current_idx-7:current_idx]['quantity'].max())
        features.append(
            product_data.iloc[current_idx-7:current_idx]['quantity'].min())

        current_date = product_data.index[current_idx]
        features.append(current_date.dayofweek)
        features.append(current_date.day)
        features.append(current_date.month)
        features.append(1 if current_date.dayofweek >= 5 else 0)

        return features

    def _extract_features_simple(self, product_data, current_idx, lookback):
        """Simplified feature extraction with flexible lookback period"""
        features = []

        # Get historical data (up to lookback days)
        start_idx = max(0, current_idx - lookback)
        historical_qty = product_data.iloc[start_idx:current_idx]['quantity'].values

        # Pad with zeros if not enough history
        if len(historical_qty) < lookback:
            historical_qty = np.pad(historical_qty, (lookback - len(historical_qty), 0), 'constant', constant_values=0)

        features.extend(historical_qty)

        # Statistical features
        historical_data = product_data.iloc[start_idx:current_idx]['quantity']
        features.append(historical_data.mean() if len(historical_data) > 0 else 0)
        features.append(historical_data.std() if len(historical_data) > 1 else 0)
        features.append(historical_data.max() if len(historical_data) > 0 else 0)
        features.append(historical_data.min() if len(historical_data) > 0 else 0)

        # Time-based features
        current_date = product_data.index[current_idx]
        features.append(current_date.dayofweek)
        features.append(current_date.day)
        features.append(current_date.month)
        features.append(1 if current_date.dayofweek >= 5 else 0)

        return features

    def _extract_features_minimal(self, product_data, current_idx):
        """Minimal feature extraction for very limited data (1-2 days)"""
        features = []

        # Lấy tất cả quantity có sẵn (1-2 giá trị)
        all_qty = product_data['quantity'].values

        # Pad thành 2 values để consistent với model
        if len(all_qty) == 1:
            features.extend([0, all_qty[0]])  # [0, current_qty]
        else:
            features.extend(all_qty[:2])  # [first, second]

        # Statistical features
        features.append(all_qty.mean())
        features.append(0)  # std = 0 cho 1 giá trị
        features.append(all_qty.max())
        features.append(all_qty.min())

        # Time-based features
        current_date = product_data.index[current_idx]
        features.append(current_date.dayofweek)
        features.append(current_date.day)
        features.append(current_date.month)
        features.append(1 if current_date.dayofweek >= 5 else 0)

        return features

    def train(self, sales_history):
        X, y = self.prepare_training_data(sales_history)

        # Giảm yêu cầu xuống 1 training sample để train được với ít data
        if X is None or len(X) < 1:
            return False

        X_scaled = self.scaler.fit_transform(X)

        # Điều chỉnh parameters để train được với ít samples
        n_samples = len(X)
        self.model = RandomForestRegressor(
            n_estimators=min(50, max(10, n_samples * 2)),  # Adaptive
            max_depth=min(5, max(2, n_samples)),  # Adaptive
            min_samples_split=max(2, min(3, n_samples // 2)),  # Ít nhất 2
            min_samples_leaf=1,  # Giảm xuống 1
            random_state=42,
            n_jobs=-1
        )

        self.model.fit(X_scaled, y)

        self._calculate_product_stats(sales_history)

        self.save_model()

        return True

    def _calculate_product_stats(self, sales_history):
        df = pd.DataFrame(sales_history)
        df['date'] = pd.to_datetime(df['created_at'])

        for product_id in df['product_id'].unique():
            product_data = df[df['product_id'] == product_id]

            daily_sales = product_data.groupby(product_data['date'].dt.date)[
                'quantity'].sum()

            self.product_stats[str(product_id)] = {
                'avg_daily_sales': float(daily_sales.mean()),
                'std_daily_sales': float(daily_sales.std()),
                'max_daily_sales': float(daily_sales.max()),
                'min_daily_sales': float(daily_sales.min()),
                'total_sales': int(product_data['quantity'].sum()),
                'last_30_days_avg': float(daily_sales.tail(30).mean()) if len(daily_sales) >= 30 else float(daily_sales.mean())
            }

    def predict_demand(self, product_id, current_stock, sales_history, days_ahead=30):
        if not self.model:
            return self._fallback_prediction(product_id, current_stock, sales_history, days_ahead)

        df = pd.DataFrame(sales_history)
        df['date'] = pd.to_datetime(df['created_at'])

        product_data = df[df['product_id'] == product_id].sort_values('date')

        if len(product_data) < 7:
            return self._fallback_prediction(product_id, current_stock, sales_history, days_ahead)

        daily_sales = product_data.groupby(product_data['date'].dt.date)[
            'quantity'].sum()
        daily_sales.index = pd.to_datetime(daily_sales.index)
        daily_sales = daily_sales.asfreq('D', fill_value=0)

        predictions = []
        current_data = daily_sales.copy()

        for day in range(days_ahead):
            if len(current_data) < 7:
                break

            features = self._extract_features_for_prediction(
                current_data, len(current_data) - 1)
            features_scaled = self.scaler.transform([features])

            pred_quantity = max(0, self.model.predict(features_scaled)[0])

            pred_date = current_data.index[-1] + timedelta(days=1)
            predictions.append({
                'date': pred_date.strftime('%Y-%m-%d'),
                'predicted_quantity': round(pred_quantity, 2)
            })

            current_data.loc[pred_date] = pred_quantity

        return predictions

    def _extract_features_for_prediction(self, product_data, current_idx):
        features = []

        last_7_days = product_data.iloc[current_idx-6:current_idx+1].values
        features.extend(last_7_days)

        features.append(product_data.iloc[current_idx-6:current_idx+1].mean())
        features.append(product_data.iloc[current_idx-6:current_idx+1].std())
        features.append(product_data.iloc[current_idx-6:current_idx+1].max())
        features.append(product_data.iloc[current_idx-6:current_idx+1].min())

        current_date = product_data.index[current_idx]
        features.append(current_date.dayofweek)
        features.append(current_date.day)
        features.append(current_date.month)
        features.append(1 if current_date.dayofweek >= 5 else 0)

        return features

    def _fallback_prediction(self, product_id, current_stock, sales_history, days_ahead):
        df = pd.DataFrame(sales_history)
        df['date'] = pd.to_datetime(df['created_at'])

        product_data = df[df['product_id'] == product_id]

        if len(product_data) == 0:
            avg_daily = 5
        else:
            daily_sales = product_data.groupby(product_data['date'].dt.date)[
                'quantity'].sum()
            avg_daily = daily_sales.mean()

        predictions = []
        last_date = datetime.now()

        for day in range(days_ahead):
            pred_date = last_date + timedelta(days=day+1)
            predictions.append({
                'date': pred_date.strftime('%Y-%m-%d'),
                'predicted_quantity': round(avg_daily, 2)
            })

        return predictions

    def calculate_reorder_recommendation(self, product_id, current_stock, predictions, lead_time_days=7):
        if not predictions:
            return None

        demand_7_days = sum(p['predicted_quantity'] for p in predictions[:7])
        demand_14_days = sum(p['predicted_quantity'] for p in predictions[:14])
        demand_30_days = sum(p['predicted_quantity'] for p in predictions[:30])

        daily_avg = demand_7_days / 7

        safety_stock = daily_avg * 3
        reorder_point = (daily_avg * lead_time_days) + safety_stock

        optimal_order_quantity = demand_30_days

        days_until_stockout = int(
            current_stock / daily_avg) if daily_avg > 0 else 999

        should_reorder = current_stock <= reorder_point
        urgency = 'high' if days_until_stockout <= 3 else 'medium' if days_until_stockout <= 7 else 'low'

        return {
            'product_id': product_id,
            'current_stock': current_stock,
            'should_reorder': should_reorder,
            'urgency': urgency,
            'reorder_point': round(reorder_point, 2),
            'safety_stock': round(safety_stock, 2),
            'optimal_order_quantity': round(optimal_order_quantity, 2),
            'predicted_demand_7_days': round(demand_7_days, 2),
            'predicted_demand_14_days': round(demand_14_days, 2),
            'predicted_demand_30_days': round(demand_30_days, 2),
            'days_until_stockout': days_until_stockout,
            'daily_average_demand': round(daily_avg, 2),
            'recommendation': self._generate_recommendation_text(
                should_reorder,
                days_until_stockout,
                optimal_order_quantity
            )
        }

    def _generate_recommendation_text(self, should_reorder, days_until_stockout, order_qty):
        if should_reorder:
            if days_until_stockout <= 3:
                return f'CẤP BÁT! Dự kiến hết hàng trong {days_until_stockout} ngày. Nên nhập ngay {int(order_qty)} sản phẩm.'
            elif days_until_stockout <= 7:
                return f'Cần nhập hàng sớm. Còn khoảng {days_until_stockout} ngày trước khi hết hàng. Đề xuất nhập {int(order_qty)} sản phẩm.'
            else:
                return f'Nên chuẩn bị nhập hàng. Đề xuất nhập {int(order_qty)} sản phẩm cho 30 ngày tới.'
        else:
            return f'Tồn kho đủ dùng cho {days_until_stockout} ngày. Chưa cần nhập hàng.'

    def save_model(self):
        if self.model:
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            joblib.dump(self.product_stats,
                        self.model_path.replace('.pkl', '_stats.pkl'))

    def load_model(self):
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                stats_path = self.model_path.replace('.pkl', '_stats.pkl')
                if os.path.exists(stats_path):
                    self.product_stats = joblib.load(stats_path)
                return True
        except Exception as e:
            print(f"Error loading model: {e}")
        return False


ai_forecast_service = DemandForecastAI()
