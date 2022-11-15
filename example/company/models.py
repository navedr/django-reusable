from django.db import models


class Person(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    position = models.CharField(max_length=30, null=True, blank=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Musician(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    instrument = models.CharField(max_length=100)
    concerts = models.ManyToManyField('Concert', through='MusicianConcert')


class Album(models.Model):
    artist = models.ForeignKey(Musician, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    release_date = models.DateField()
    num_stars = models.IntegerField()


class City(models.Model):
    name = models.CharField(max_length=100)


class Concert(models.Model):
    name = models.CharField(max_length=100)


class MusicianConcert(models.Model):
    musician = models.ForeignKey(Musician, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    concert = models.ForeignKey(Concert, on_delete=models.CASCADE)
