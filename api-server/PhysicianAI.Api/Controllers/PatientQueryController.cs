using Microsoft.AspNetCore.Mvc;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace PhysicianAI.Api.Controllers
{
    [ApiController]
    [Route("api/patient/query")]
    public class PatientQueryController : ControllerBase
    {
        private readonly HttpClient _httpClient;

        public PatientQueryController(IHttpClientFactory httpClientFactory)
        {
            _httpClient = httpClientFactory.CreateClient();
        }

        [HttpPost]
        public async Task<IActionResult> QueryPatient([FromBody] UserQuestion question)
        {
            var payload = new {
                session_id = question.SessionId,
                message = question.Text
            };
            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var response = await _httpClient.PostAsync("http://localhost:5000/generate-answer", content);
            // var response = await _httpClient.PostAsync("http://localhost:5000/debug", content);


            if (response.IsSuccessStatusCode)
            {
                var fastapiResult = await response.Content.ReadAsStringAsync();
                return Ok(fastapiResult);
            }
            else {
                return StatusCode((int)response.StatusCode, "Failed to get response from LLM service");
            }
        }
    }
    public class UserQuestion
    {
        public required string SessionId { get; set; }
        public required string Text { get; set; }
    }

    public class FastApiResponse
    {
        public required string Answer {get; set; }
    }
}