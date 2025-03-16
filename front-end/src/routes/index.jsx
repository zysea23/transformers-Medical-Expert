import React from "react";
import Layout from "../components/Layout";
import HomePage from "../pages/HomePage";
import ResultPage from "../pages/ResultPage";


const routes = [
    {
        path: "/",
        element: <Layout/>,
        children:[
            { index: true, element: <HomePage /> },
            { path: 'results', element: <ResultPage /> },
        ]
    }
];

export default routes;