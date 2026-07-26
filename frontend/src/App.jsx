import React from "react";
import { Route, Routes } from "react-router-dom";

import NavBar from "./components/NavBar.jsx";
import CreateListing from "./pages/CreateListing.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Home from "./pages/Home.jsx";
import ListingDetail from "./pages/ListingDetail.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";

export default function App() {
  return (
    <>
      <NavBar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/listings/new" element={<CreateListing />} />
        <Route path="/listings/:id" element={<ListingDetail />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </>
  );
}
