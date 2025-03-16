import React from 'react';
import { BrowserRouter as Router, useRoutes } from 'react-router-dom';
import routes from './routes/index';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import ResultPage from './pages/ResultPage';
import './styles/global.scss';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';
import 'bootstrap-icons/font/bootstrap-icons.css';

const AppRoutes = () => {
  const element = useRoutes(routes);
  return element;
};

function App() {
  return (
    <Router>
      <AppRoutes />
      
    </Router>
    // <Router>
    //   <Routes>
    //     <Route path="/" element={<Layout />}>
    //       <Route index element={<HomePage />} />
    //       <Route path="results" element={<ResultPage />} />
    //     </Route>
    //   </Routes>
    // </Router>
  );
}

export default App;