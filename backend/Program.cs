var builder = WebApplication.CreateBuilder(args);

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.MapGet("/api/todos", () =>
{
    return Results.Ok(new[]
    {
        new { Id = 1, Text = "İlk todo" },
        new { Id = 2, Text = "İkinci todo" }
    });
});

app.MapPost("/api/todos", (TodoRequest request) =>
{
    return Results.Created("/api/todos/1", new
    {
        Id = 1,
        Text = request.Text
    });
});

app.MapDelete("/api/todos/{id:int}", (int id) =>
{
    return Results.NoContent();
});

app.Run();

record TodoRequest(string Text);