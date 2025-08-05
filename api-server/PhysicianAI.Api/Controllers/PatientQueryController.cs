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
        public async Task QueryPatient([FromBody] UserQuestion question)
        {
            var payload = new {
                patient_id = question.PatientId,
                session_id = question.SessionId,
                message = question.Text
            };
            var json = JsonSerializer.Serialize(payload);

            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var request = new HttpRequestMessage(HttpMethod.Post, "http://localhost:5000/generate-answer")
            {
                Content = content
            };

            var response = await _httpClient.SendAsync(request, HttpCompletionOption.ResponseHeadersRead);


            Response.ContentType = "text/plain";
            Response.StatusCode = (int)response.StatusCode;

            using var responseStream = await response.Content.ReadAsStreamAsync();
            await responseStream.CopyToAsync(Response.Body);
        }
    }
    public class UserQuestion
    {
        public required string PatientId { get; set; }
        public required string SessionId { get; set; }
        public required string Text { get; set; }
    }

    public class FastApiResponse
    {
        public required string Answer {get; set; }
    }
}