const API_URL = "http://localhost:8000"

export async function getAlertHistory() {
  const res = await fetch(`${API_URL}/alerts`)
  console.log("Alert history response:", res)
  return res.json()
}