import React, { useEffect, useState } from "react";
import axios from "axios";
import "./index.css";  
import { FaUser, FaPhone, FaEnvelope, FaMoneyBillAlt } from "react-icons/fa";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { ThemeProvider } from "./components/theme.js";
import ThemeToggle from "./components/toggle.js";


const BillingRecords = () => {
    const [bills, setBills] = useState([]);
    const [formData, setFormData] = useState({ name: "", contact: "", email: "", amount: "" });
    const [editingBillId, setEditingBillId] = useState(null);
    const [showTable, setShowTable] = useState(false);
    const [showChart, setShowChart] = useState(false);
    

    useEffect(() => {
        fetchBills();
    }, []);

    const fetchBills = async () => {
        try {
            const response = await axios.get("http://127.0.0.1:5000/get_bills");
            setBills(response.data);
        } catch (error) {
            console.error("Error fetching billing records:", error);
        }
    };

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };


    const addBill = async () => {
        try {
            await axios.post("http://127.0.0.1:5000/add_bill", formData);
            fetchBills();
            setFormData({ name: "", contact: "", email: "", amount: "" });
        } catch (error) {
            console.error("Error adding bill:", error);
        }
    };

    const updateBill = async () => {
        if (!editingBillId) return;
        try {
            await axios.put(`http://127.0.0.1:5000/update_bill/${editingBillId}`, {
                name: formData.name,
                contact: formData.contact,
                email: formData.email,
                amount: formData.amount
            });
            fetchBills();
            setFormData({ name: "", contact: "", email: "", amount: "" });
            setEditingBillId(null);
        } catch (error) {
            console.error("Error updating bill:", error);
        }
    };

    const deleteBill = async (billId) => {
        try {
            await axios.delete(`http://127.0.0.1:5000/delete_bill/${billId}`);
            fetchBills();
        } catch (error) {
            console.error("Error deleting bill:", error);
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
            <ThemeToggle />
            <h2>Billing Records</h2>
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
                    <button type="button" className="update" onClick={updateBill}>Update</button>
                ) : (
                    <button type="button" className="add" onClick={addBill}>Add</button>
                )}
                </form>

            <div className="toggle-button-wrapper">
                <button className="toggle-table" onClick={() => setShowTable(!showTable)}>
                    {showTable ? "Hide Bills" : "Show Bills"}
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

export default BillingRecords;
