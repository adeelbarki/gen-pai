using Microsoft.AspNetCore.Mvc;

namespace PhysicianAI.Api.Controllers
{
    [ApiController]
    [Route("api/patient/query")]
    public class PatientQueryController : ControllerBase
    {
        [HttpPost]
        public IActionResult QueryPatient([FromBody] UserQuestion question)
        {
            return Ok(new { answer = $"Received question: {question.Text}" });

        }
    }
    public class UserQuestion
    {
        public string Text { get; set; }
    }
}