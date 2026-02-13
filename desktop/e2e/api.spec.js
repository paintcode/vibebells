/**
 * Backend API Integration Tests
 * 
 * Tests the backend API endpoints independently
 */

const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const BACKEND_URL = 'http://localhost:5000';
const MIDI_FILE_PATH = path.join(__dirname, 'fixtures', 'test-song.mid');

test.describe('Backend API', () => {
  
  test('health check returns healthy status', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/health`);
    
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('status');
    expect(data.status).toBe('healthy');
  });
  
  test('generate arrangements with MIDI file', async ({ request }) => {
    // Read MIDI file
    const midiBuffer = fs.readFileSync(MIDI_FILE_PATH);
    
    // Prepare multipart form data
    const formData = {
      file: {
        name: 'test-song.mid',
        mimeType: 'audio/midi',
        buffer: midiBuffer
      },
      players: JSON.stringify([
        { name: 'Alice', experience: 'experienced' },
        { name: 'Bob', experience: 'intermediate' },
        { name: 'Carol', experience: 'beginner' },
        { name: 'Dave', experience: 'beginner' }
      ])
    };
    
    const response = await request.post(`${BACKEND_URL}/api/generate-arrangements`, {
      multipart: formData,
      timeout: 30000
    });
    
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    
    // Verify response structure
    expect(data).toHaveProperty('arrangements');
    expect(Array.isArray(data.arrangements)).toBeTruthy();
    expect(data.arrangements.length).toBeGreaterThan(0);
    
    // Check first arrangement
    const arrangement = data.arrangements[0];
    expect(arrangement).toHaveProperty('strategy');
    expect(arrangement).toHaveProperty('quality_score');
    expect(arrangement).toHaveProperty('assignments');
    expect(arrangement).toHaveProperty('validation');
    
    // Verify quality score is in valid range
    expect(arrangement.quality_score).toBeGreaterThanOrEqual(0);
    expect(arrangement.quality_score).toBeLessThanOrEqual(100);
    
    // Verify validation passed
    expect(arrangement.validation.valid).toBeTruthy();
    
    console.log(`✓ Generated ${data.arrangements.length} arrangements`);
    console.log(`  Strategy: ${arrangement.strategy}, Score: ${arrangement.quality_score}`);
  });
  
  test('export arrangement to CSV', async ({ request }) => {
    // First generate an arrangement
    const midiBuffer = fs.readFileSync(MIDI_FILE_PATH);
    
    const players = [
      { name: 'Alice', experience: 'experienced' },
      { name: 'Bob', experience: 'intermediate' }
    ];
    
    const generateResponse = await request.post(`${BACKEND_URL}/api/generate-arrangements`, {
      multipart: {
        file: {
          name: 'test-song.mid',
          mimeType: 'audio/midi',
          buffer: midiBuffer
        },
        players: JSON.stringify(players)
      }
    });
    
    expect(generateResponse.ok()).toBeTruthy();
    const generateData = await generateResponse.json();
    const arrangement = generateData.arrangements[0];
    
    // Now export to CSV
    const exportResponse = await request.post(`${BACKEND_URL}/api/export-csv`, {
      headers: {
        'Content-Type': 'application/json'
      },
      data: {
        filename: 'test-song.mid',
        arrangement: arrangement,
        players: players,
        strategy: arrangement.strategy
      }
    });
    
    expect(exportResponse.ok()).toBeTruthy();
    expect(exportResponse.status()).toBe(200);
    
    // Verify content type
    const contentType = exportResponse.headers()['content-type'];
    expect(contentType).toContain('text/csv');
    
    // Get CSV content
    const csvContent = await exportResponse.text();
    expect(csvContent.length).toBeGreaterThan(0);
    
    // Verify CSV structure
    expect(csvContent).toContain('Metadata');
    expect(csvContent).toContain('Players');
    expect(csvContent).toContain('All Bells');
    expect(csvContent).toContain(arrangement.strategy);
    
    console.log(`✓ CSV export successful (${csvContent.length} bytes)`);
    console.log(`  First line: ${csvContent.split('\n')[0]}`);
  });
  
  test('handles invalid file upload', async ({ request }) => {
    const response = await request.post(`${BACKEND_URL}/api/generate-arrangements`, {
      multipart: {
        file: {
          name: 'invalid.txt',
          mimeType: 'text/plain',
          buffer: Buffer.from('not a midi file')
        },
        players: JSON.stringify([{ name: 'Player 1', experience: 'beginner' }])
      }
    });
    
    // Should return error
    expect(response.ok()).toBeFalsy();
    expect(response.status()).toBeGreaterThanOrEqual(400);
    
    const data = await response.json();
    expect(data).toHaveProperty('error');
    
    console.log(`✓ Invalid file rejected: ${data.error}`);
  });
  
  test('handles missing players configuration', async ({ request }) => {
    const midiBuffer = fs.readFileSync(MIDI_FILE_PATH);
    
    const response = await request.post(`${BACKEND_URL}/api/generate-arrangements`, {
      multipart: {
        file: {
          name: 'test-song.mid',
          mimeType: 'audio/midi',
          buffer: midiBuffer
        }
        // No players field
      }
    });
    
    // Should return error
    expect(response.ok()).toBeFalsy();
    expect(response.status()).toBeGreaterThanOrEqual(400);
    
    const data = await response.json();
    expect(data).toHaveProperty('error');
    // More flexible check - just verify error message exists
    expect(data.error).toBeTruthy();
    expect(data.error.length).toBeGreaterThan(0);
    
    console.log(`✓ Missing players rejected: ${data.error}`);
  });
});
