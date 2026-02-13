import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { ConfigProvider, App as AntApp } from 'antd';
import { store } from '@/store';
import { AppErrorBoundary } from '@/components/common/AppErrorBoundary';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Provider store={store}>
      <ConfigProvider
        theme={{
          token: {
            colorPrimary: '#1677ff',
            borderRadius: 6,
            fontFamily:
              "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
          },
          components: {
            Table: {
              headerBg: '#fafafa',
              rowHoverBg: '#f0f5ff',
            },
          },
        }}
      >
        <AntApp>
          <AppErrorBoundary>
            <App />
          </AppErrorBoundary>
        </AntApp>
      </ConfigProvider>
    </Provider>
  </React.StrictMode>,
);
