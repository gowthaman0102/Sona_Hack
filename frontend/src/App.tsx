import './App.css'
import {
  Navigate,
  Route,
  Routes,
} from 'react-router-dom'

import AppLayout from './components/AppLayout'
import MultiTaskPage from './pages/MultiTaskPage'
import OverviewPage from './pages/OverviewPage'
import RoutePromptPage from './pages/RoutePromptPage'


export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route element={<OverviewPage />} index />
        <Route element={<RoutePromptPage />} path="route" />
        <Route element={<MultiTaskPage />} path="multi-task" />
        <Route element={<Navigate replace to="/" />} path="*" />
      </Route>
    </Routes>
  )
}
