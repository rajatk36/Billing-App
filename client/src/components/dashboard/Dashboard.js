import React, { useEffect, useState } from "react";
import api from "../../api";
import "./dashboard.css";  
import { FaUser, FaPhone, FaEnvelope, FaMoneyBillAlt, FaSignOutAlt, FaUsers, FaFileInvoice, FaRupeeSign  } from "react-icons/fa";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { ThemeProvider } from "../theme/theme.js";
import ThemeToggle from "../theme/toggle.js";
import { useNavigate } from "react-router-dom";


const Dashboard = () => {
    const [bills, setBills] = useState([]);
    const [formData, setFormData] = useState({ name: "", contact: "", email: "", amount: "" });
    const [editingBillId, setEditingBillId] = useState(null);
    const [showTable, setShowTable] = useState(false);
    const [showChart, setShowChart] = useState(false);
    const [userStats, setUserStats] = useState({ customer_count: 0, bill_count: 0, total_amount: 0 });
    const [userEmail, setUserEmail] = useState("");
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [loadingAdd, setLoadingAdd] = useState(false);
    const [loadingDelete, setLoadingDelete] = useState(false);
    const [loadingUpdate, setLoadingUpdate] = useState(false);
    const [error, setError] = useState("");
    const [errorDelete, setErrorDelete] = useState("");

    useEffect(() => {
        const init = async () => {
            await fetchUserInfo();
            await fetchBills();
            await fetchUserStats();
        };
        init();
    }, []);

    const fetchUserInfo = async () => {
        try {
            const response = await api.checkAuth();
            if (response.authenticated) {
                setUserEmail(response.user.email);
            }
        } catch (error) {
            console.error("Error fetching user info:", error);
        }
    };

    const fetchUserStats = async () => {
        try {
            console.log("Fetching user stats...");
            const response = await api.getUserStats();
            console.log("User stats fetched successfully:", response);
            setUserStats(response);
        } catch (error) {
            console.error("Error fetching user stats:", error);
            
        }
    };

    const fetchBills = async () => {
        try {
            console.log("Fetching bills...");
            const response = await api.getBills();
            console.log("Bills fetched successfully:", response);
            setBills(response);
        } catch (error) {
            console.error("Error fetching billing records:", error);
           
        }
    };

    
    const onToggleBills = async () => {
        const next = !showTable;
        setShowTable(next);
        if (next) {
        setLoading(true);
        await fetchBills();
        await fetchUserStats();
        setLoading(false);
        }
    };
  

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const addBill = async () => {
        // Validate form data
        if (!formData.name || !formData.contact || !formData.email || !formData.amount) {
            alert("Please fill in all fields");
            return;
        }
        const Validname=/^[A-Za-z\s]{3,}$/;
        const Validcontact = /^\d{10}$/;
        const Validemail=/^[a-zA-Z0-9._%+-]+@gmail\.com$/;

        if(!Validname.test(formData.name)){
            setError("Name must be filled");
            
            return;
        }
        setError("");
        if (!Validcontact.test(formData.contact)) {
            setError("Contact must be exactly 10 digits");
            
            return;
        }
        setError("");
        if (!Validemail.test(formData.email)) {
            setError("Email must be a valid @gmail.com address");
            
            return;
        }
        setError("");
        if(!/^\d+$/.test(formData.amount) || Number(formData.amount) <= 0){
            setError("Amount must not be empty")
            
            return;
        }
        setError("");
        try {
            setLoadingAdd(true);
            console.log("Adding bill with data:", formData);
            const response = await api.addBill(formData);
            console.log("Bill added successfully:", response);
            setLoadingAdd(false);
            // Refresh data
            await fetchBills();
            await fetchUserStats();
            
            // Clear form
            setFormData({ name: "", contact: "", email: "", amount: "" });
            
            alert("Bill added successfully!");
        } catch (error) {
            console.error("Error adding bill:", error);
            alert(`Failed to add bill: ${error.message}`);
        }
    };

    const updateBill = async () => {
        if (!editingBillId) return;
        
       
        if (!formData.name || !formData.contact || !formData.email || !formData.amount) {
            alert("Please fill in all fields");
            return;
        }

        try {
            setLoadingUpdate(true);
            console.log("Updating bill with data:", formData);
            const response = await api.updateBill(editingBillId, {
                name: formData.name,
                contact: formData.contact,
                email: formData.email,
                amount: formData.amount
            });
            console.log("Bill updated successfully:", response);
            setLoadingUpdate(false);
            await fetchBills();
            await fetchUserStats();
            
            
            setFormData({ name: "", contact: "", email: "", amount: "" });
            setEditingBillId(null);
            
            alert("Bill updated successfully!");
        } catch (error) {
            console.error("Error updating bill:", error);
            alert(`Failed to update bill: ${error.message}`);
        }
    };

    const deleteBill = async (billId) => {
        if (!window.confirm("Are you sure you want to delete this bill?")) {
            return;
        }

        try {
            console.log("Deleting bill:", billId);
            const response = await api.deleteBill(billId);
            console.log("Bill deleted successfully:", response);
            
        
            await fetchBills();
            await fetchUserStats();
            
            alert("Bill deleted successfully!");
        } catch (error) {
            console.error("Error deleting bill:", error);
            alert(`Failed to delete bill: ${error.message}`);
        }
    };

    const handleLogout = async () => {
        try {
            await api.logout();
            alert("Logged out successfully!");
            navigate("/");
        } catch (error) {
            console.error("Logout failed:", error);
            
            navigate("/");
        }
    };
    //deleting account
    const handleDeleteAccount = async () => {
    const confirmDelete = window.confirm(
      "⚠️ This will permanently delete your account, including all your data and bills. Do you want to continue?"
    );
    if (!confirmDelete) return;

    setLoadingDelete(true);
    setErrorDelete("");

    try {
      const res = await api.deleteAccount();

      if (res.success) {
        alert("✅ Account deleted successfully.");
        navigate("/"); 
      } else {
        setErrorDelete(res.error || "Failed to delete account.");
      }
    } catch (err) {
      setErrorDelete(err.message || "Error deleting account.");
      navigate("/");
    } finally {
      setLoadingDelete(false);
    }
  };

    const viewAllUsersData = async () => {
        try {
            const response = await api.viewAllUsersData();
            alert("All Users Data:\n" + JSON.stringify(response, null, 2));
        } catch (error) {
            console.error("Error fetching all users data:", error);
            alert(`Failed to fetch all users data: ${error.message}`);
        }
    };

    const chartData = Object.values(
    bills.reduce((acc, bill) => {
        const name = bill.name;
        const amount = parseFloat(bill.amount) || 0;
        acc[name] = acc[name]
        ? { name, amount: acc[name].amount + amount }
        : { name, amount };
        return acc;
    }, {})
    );


    return (
    <ThemeProvider>
        <div className="container">
            <div className="theme-toggle-wrapper">
                <ThemeToggle />
                <div className="user-info">
                    <span className="user-email">Welcome, {userEmail || 'User'}!</span>
                </div>
                <button 
                    className="logout-btn" 
                    onClick={handleLogout}
                    title="Logout"
                >
                    <FaSignOutAlt /> Logout
                </button>
                <button 
                className="logout-btn" 
                onClick={handleDeleteAccount}>

                  {loadingDelete}  
                    {<FaSignOutAlt />}
                Delete Account
                </button>
                {errorDelete && <p className="text-red-500 mt-2">{errorDelete}</p>}

            </div>
             <p> {error}  </p>
            <h2>Billing Records</h2>
            
           
            <div className="stats-container">
                {console.log("Current userStats:", userStats)}
                <div className="stat-card">
                    <FaUsers className="stat-icon" />
                    <div className="stat-content">
                        <h3>{userStats.customer_count || 0}</h3>
                        <p>Total Customers</p>
                    </div>
                </div>
                <div className="stat-card">
                    <FaFileInvoice className="stat-icon" />
                    <div className="stat-content">
                        <h3>{userStats.bill_count || 0}</h3>
                        <p>Total Bills</p>
                    </div>
                </div>
                <div className="stat-card">
                    <FaRupeeSign  className="stat-icon" />
                    <div className="stat-content">
                        <h3> {(userStats.total_amount || 0).toFixed(2)}</h3>
                        <p>Total Amount</p>
                    </div>
                </div>
            </div>
                <form className="form-container">
                <div className="input-group">
                    <FaUser className="icon" />
                    <input type="text" name="name" placeholder="Customer Name" value={formData.name} onChange={handleChange} />
                </div>

                <div className="input-group">
                    <FaPhone className="icon" />
                    <input type="text" name="contact" placeholder="Contact" value={formData.contact} onChange={handleChange} />
                </div>

                <div className="input-group">
                    <FaEnvelope className="icon" />
                    <input type="email" name="email" placeholder="Email" value={formData.email} onChange={handleChange} />
                </div>

                <div className="input-group">
                    <FaMoneyBillAlt className="icon" />
                    <input type="number" name="amount" placeholder="Amount" value={formData.amount} onChange={handleChange} />
                </div>

                {editingBillId ? (
                    <button type="button" className="update" onClick={updateBill} disabled={loadingUpdate}>
                        {loadingUpdate ? "Updating...": "Update"}
                        </button>
                ) : (
                    <button type="button" className="add" onClick={addBill} disabled={loadingAdd}>
                        {loadingAdd ? "Adding...": "Add"}
                        </button>
                )}
                </form>

            <div className="toggle-button-wrapper">
                <button className="toggle-table" onClick={onToggleBills} disabled={loading}>
                    {loading ? "loading...": showTable ? "Hide Bills" : "Show Bills"}
                    
                </button>
                <button className="admin-view-btn" onClick={viewAllUsersData}>
                    View All Users Data
                </button>
            </div>
            

            {showTable && (
                <table>
                <thead>
                    <tr>
                        <th>Bill ID</th>
                        <th>Name</th>
                        <th>Contact</th>
                        <th>Email</th>
                        <th>Amount</th>
                        <th>Date</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {bills.length > 0 ? (
                        bills.map((bill) => (
                         <tr key={bill.id}>
                             <td>{bill.id}</td>
                             <td>{bill.name}</td>
                             <td>{bill.contact}</td>
                             <td>{bill.email}</td>
                             <td>{bill.amount}</td>
                             <td>{bill.date ? new Date(bill.date).toLocaleString('en-US', { hour: 'numeric', minute: 'numeric', hour12: true, year: 'numeric', month: '2-digit', day: '2-digit' }) : ''}</td>
                             <td>
                            <button onClick={() => {
                              setEditingBillId(bill.id);
                              setFormData({
                                  name: bill.name,
                                  contact: bill.contact,
                                  email: bill.email,
                                  amount: bill.amount });
                                   }} className="update">Edit</button>
                                 <button onClick={() => deleteBill(bill.id)} className="delete">Delete</button>
                             </td>
                         </tr>
                        ))
                       ) : (
                        <tr>
                            <td colSpan="7" style={{ textAlign: "center" }}>No records found</td>
                        </tr>
                    )}
                </tbody>
            </table>
            )}
        
        <div className="toggle-button-wrapper">
      <button className="toggle-chart" onClick={() => setShowChart(!showChart)}>
        {showChart ? "Hide Chart" : "Show Chart"}
      </button> 
        </div>
        {showChart && chartData.length > 0 && (
           <div className="chart-container">
                <h3 style={{ textAlign: 'center' }}>Total Amount by Customer</h3>
                <ResponsiveContainer width={chartData.length* 120} height={300}>
                <BarChart
                    width={200}
                    height={300}
                    data={chartData}
                    barCategoryGap={2}
                    barGap={1}           
                >
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip
                    contentStyle={{
                        backgroundColor: 'var(--tooltip-bg, rgba(255, 255, 255, 0.8))',
                        color: 'var(--tooltip-text, #000)',
                    }}
                    itemStyle={{ color: 'var(--tooltip-text, #000)' }}
                    cursor={{ fill: 'rgba(0,0,0,0.1)' }}
                    wrapperStyle={{
                        borderRadius: '5px',
                        border: '1px solid #ccc',
                    }}
                 />


                <Bar dataKey="amount" fill="#82ca9d"  barSize={20} activeBar={{ fill: '#82ca9d', stroke: 'none' }}/>
                </BarChart>
                </ResponsiveContainer>
            </div>
            )}
    
        </div>
        </ThemeProvider>  
    );
};

export default Dashboard;
