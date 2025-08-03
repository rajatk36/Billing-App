import React from "react";
import { useTheme } from "./theme";
import { FaMoon, FaSun } from "react-icons/fa";
import "./theme.css";

const ThemeToggle = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <button onClick={toggleTheme} className="theme-toggle" >
      {theme === "light" ? <FaMoon /> : <FaSun />}
    </button>
  );
};

export default ThemeToggle;
