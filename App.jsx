import React, { useState } from 'react'
import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom'
import Portfolio from './Portfolio.jsx'
import PMVikas from './PMVikas.jsx'
import Insights from './Insights.jsx'
import './App.css'

function Nav() {
  const loc = useLocation()
  const [showContact, setShowContact] = useState(false)

  return (
    <>
      <nav className="nav">
        <div className="nav-brand">
          <span className="nav-initials">E.</span>
          <span className="nav-name">Evangelina</span>
        </div>
        <div className="nav-links">
          <NavLink to="/" className={({isActive}) => isActive ? 'nav-link active' : 'nav-link'} end>
            <span className="nav-num">01</span> Portfolio
          </NavLink>
          <NavLink to="/pm-vikas" className={({isActive}) => isActive ? 'nav-link active' : 'nav-link'}>
            <span className="nav-num">02</span> PM Tracker
          </NavLink>
          <NavLink to="/insights" className={({isActive}) => isActive ? 'nav-link active' : 'nav-link'}>
            <span className="nav-num">03</span> Insights
          </NavLink>
        </div>
        <button className="nav-cta" type="button" onClick={() => setShowContact(true)}>Hire Me</button>
      </nav>

      {showContact && (
        <div className="contact-modal-backdrop" onClick={() => setShowContact(false)}>
          <div className="contact-modal" role="dialog" aria-modal="true" aria-labelledby="contact-modal-title" onClick={(event) => event.stopPropagation()}>
            <button className="contact-modal-close" type="button" onClick={() => setShowContact(false)} aria-label="Close contact box">x</button>
            <span className="contact-modal-tag">Contact Evangelina</span>
            <h2 id="contact-modal-title">Let's Connect</h2>
            <p>Open a direct contact source below for projects, collaborations, or opportunities.</p>
            <div className="contact-modal-detail">
              <span>Email</span>
              <strong>evangelinatjais@gmail.com</strong>
            </div>
            <div className="contact-modal-actions">
              <a href="mailto:evangelinatjais@gmail.com?subject=Portfolio%20Contact" className="contact-modal-link">Open Mail</a>
              <a href="tel:+917907152494" className="contact-modal-link">Call</a>
              <a href="https://www.linkedin.com/in/evangelina-jais-440487355" className="contact-modal-link" target="_blank" rel="noreferrer">LinkedIn</a>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Nav />
      <main>
        <Routes>
          <Route path="/" element={<Portfolio />} />
          <Route path="/pm-vikas" element={<PMVikas />} />
          <Route path="/insights" element={<Insights />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
