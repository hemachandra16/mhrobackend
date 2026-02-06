const express = require('express');
const cors = require('cors');
const srmacademia = require('srm-academia-api');

const app = express();
app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', message: 'Academia SRM Scraper API is running' });
});

// Login endpoint
app.post('/api/login', async (req, res) => {
    const { username, password } = req.body;

    if (!username || !password) {
        return res.status(400).json({ error: 'Username and password required' });
    }

    try {
        const student = new srmacademia(username, password);
        await student.login();

        res.json({
            success: true,
            message: 'Login successful'
        });
    } catch (error) {
        res.status(401).json({
            success: false,
            message: 'Invalid credentials'
        });
    }
});

// Attendance endpoint
app.post('/api/attendance', async (req, res) => {
    const { username, password } = req.body;

    if (!username || !password) {
        return res.status(400).json({ error: 'Credentials required' });
    }

    try {
        const student = new srmacademia(username, password);
        await student.login();

        const attendance = await student.attendance();

        // Transform the data to match our frontend format
        const transformedData = attendance.map(subject => ({
            code: subject.code || '',
            name: subject.title || '',
            type: subject.category || 'Theory',
            faculty: subject.faculty || 'N/A',
            slot: subject.slot || 'N/A',
            conducted: subject.totalHours || 0,
            attended: subject.attendedHours || 0,
            percentage: parseFloat(subject.percentage) || 0
        }));

        res.json({
            success: true,
            data: transformedData,
            count: transformedData.length
        });
    } catch (error) {
        console.error('Attendance error:', error);
        res.status(500).json({ error: error.message || 'Failed to fetch attendance' });
    }
});

// Marks endpoint
app.post('/api/marks', async (req, res) => {
    const { username, password } = req.body;

    if (!username || !password) {
        return res.status(400).json({ error: 'Credentials required' });
    }

    try {
        const student = new srmacademia(username, password);
        await student.login();

        const marks = await student.marks();

        // Transform the data to match our frontend format
        const transformedData = marks.map(subject => ({
            code: subject.code || '',
            name: subject.title || '',
            type: subject.category || 'Theory',
            test1: subject.test1 || null,
            test2: subject.test2 || null,
            test3: subject.assignment || null
        }));

        res.json({
            success: true,
            data: transformedData,
            count: transformedData.length
        });
    } catch (error) {
        console.error('Marks error:', error);
        res.status(500).json({ error: error.message || 'Failed to fetch marks' });
    }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, '0.0.0.0', () => {
    console.log('Academia SRM Scraper API starting...');
    console.log(`API will be available at: http://localhost:${PORT}`);
    console.log('Endpoints:');
    console.log('   - POST /api/login (test credentials)');
    console.log('   - POST /api/attendance (get attendance data)');
    console.log('   - POST /api/marks (get marks data)');
});
