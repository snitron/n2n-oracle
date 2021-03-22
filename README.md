Задача "Мост для перевода средств между двумя блокчейн сетями"
====

## Ввведение

Этот репозиторий предназначен для публикации решения командно задачи финала профиля "Программная инженерия финансовых технологий" Олимпиады НТИ 2020/21.

Задача заключается в разработке системы из контрактов для Ethereum Virtual Machine и сервиса, запускаемого в контейнеризированном окружении Docker, так чтобы они предоставляли возможность пользователям двух блокчейн сетей переводить денежные средства из одной сети в другую.

## Подготовка

Прежде чем решать задачу, создайте ветку (_branch_) `develop` в этом репозитории. После этого вы можете склонировать репозиторий к себе на локальную машину и готовить код, решающий задачу.

### Проверка решения

Каждый раз, когда вы будете делать `push` в ветку `develop` вашего репозитория у вас будет автоматически проводиться предварительная проверка решения. Результат проверки можно будет видеть в GitLab в разделе `CI/CI -> Pipelines`.

Если проверка прошла успешно, то вы увидете в самом верху списка зеленый значок с надписью `passed`.

Если проверка не прошла, то значок будет красный и надпись будет гласить `failed`. Щелкните по значку (а на новом экране на надпись `test` рядом с красным крестиком), чтобы увидеть на какой именно комманде проверка не прошла.

Чтобы ваше решение могло проходить автоматическую проверку в GitLab не удаляйте и не изменяйте файл `.gitlab-ci.yml`.

### Отправка решения на приемку

Как только вы считате, что ваше решение в той или иной степени готово, то нужно создать Merge Request для слияния изменений из ветки `develop` в ветку `master`. При создании Merge Request в качестве ответственного (assignee) укажите того, кто будет отвечать за приемку результатов.