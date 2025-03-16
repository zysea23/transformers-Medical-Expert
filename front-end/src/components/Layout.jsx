import React from "react";
import { Outlet, Link } from "react-router-dom";
import logo from "../assets/logo.png";
import "./Layout.scss";

const Layout = () => {
  return (
    <div className="app-container">
      <header className="header">
        <div className="container">
          <Link to="/">
            <img src={logo} alt="Logo" className="logo" />
          </Link>
        </div>
      </header>

      <main>
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;